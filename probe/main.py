"""Probe CLI and FastAPI app entry point."""

import asyncio
import json

import typer
from fastapi import FastAPI
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TaskProgressColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

console = Console()

cli = typer.Typer(name="probe", help="AI sycophancy detection tool", no_args_is_help=True)
api = FastAPI(title="Probe API", version="0.1.0")

app = cli  # entry point for `probe` CLI command


@cli.command()
def generate(
    count: int = typer.Option(500, help="Number of claims to generate"),
    types: str = typer.Option("math,logic,science,code", help="Comma-separated claim types"),
    output: str = typer.Option("claims.json", help="Output file path"),
    control_ratio: float = typer.Option(0.3, help="Fraction of claims that are true (controls)"),
) -> None:
    """Generate and preview test claims without running them against a model."""
    from probe.claims import generate_claims

    claim_types = [t.strip() for t in types.split(",")]
    console.print(f"Generating [bold]{count}[/bold] claims ({', '.join(claim_types)})...")

    claims = generate_claims(total=count, claim_types=claim_types, control_ratio=control_ratio)

    data = [
        {
            "claim_text": c.claim_text,
            "ground_truth": c.ground_truth,
            "false_value": c.false_value,
            "category": c.category,
            "subcategory": c.subcategory,
            "is_control": c.is_control,
        }
        for c in claims
    ]

    with open(output, "w") as f:
        json.dump(data, f, indent=2)

    # Summary table
    by_type: dict[str, int] = {}
    controls = 0
    for c in claims:
        by_type[c.category] = by_type.get(c.category, 0) + 1
        if c.is_control:
            controls += 1

    table = Table(title=f"Generated {len(claims)} claims → {output}")
    table.add_column("Type", style="cyan")
    table.add_column("Count", justify="right")
    for claim_type, cnt in sorted(by_type.items()):
        table.add_row(claim_type, str(cnt))
    table.add_row("[bold]controls[/bold]", f"[yellow]{controls}[/yellow]")
    console.print(table)


@cli.command()
def run(
    model: str = typer.Option(..., help="Model to test, e.g. openai:gpt-4o"),
    key: str = typer.Option(..., help="API key for the target model"),
    claims: int = typer.Option(500, help="Number of claims to test"),
    types: str = typer.Option("math,logic,science,code", help="Claim types (comma-separated)"),
    generation: int = typer.Option(0, help="Evolution generation number"),
    concurrency: int = typer.Option(10, help="Max concurrent API requests"),
    rpm: int = typer.Option(60, help="Max requests per minute"),
) -> None:
    """Run a sycophancy test against a target model."""
    from probe.db import init_db, get_session
    from probe.db.store import create_run, create_test_cases
    from probe.claims import generate_claims
    from probe.pressure.templates import TemplateEngine
    from probe.runner.executor import TestExecutor
    from probe.scoring.objective import score_objective
    from probe.db.models import TestResult as TestResultModel, TestRun as TestRunModel

    # Validate model format
    if ":" not in model:
        console.print("[red]Model must be in provider:model format, e.g. anthropic:claude-haiku-4-5[/red]")
        raise typer.Exit(1)

    provider, model_name = model.split(":", 1)

    # Init DB
    init_db()

    claim_types = [t.strip() for t in types.split(",")]

    console.print(f"Testing [bold]{model}[/bold]")
    console.print(f"Claims: {claims} | Types: {', '.join(claim_types)} | Concurrency: {concurrency}")

    # Generate claims
    console.print("\nGenerating claims...")
    all_claims = generate_claims(total=claims, claim_types=claim_types)
    console.print(f"  Generated {len(all_claims)} claims ({sum(1 for c in all_claims if c.is_control)} controls)")

    # Build all (claim × pressure_level) test cases
    engine = TemplateEngine()
    PRESSURE_LEVELS = list(range(8))

    test_matrix: list[dict] = []
    for claim in all_claims:
        for level in PRESSURE_LEVELS:
            prompt = engine.fill(claim.claim_text, level)
            test_matrix.append({
                "claim": claim,
                "pressure_level": level,
                "prompt": prompt,
                "messages": [{"role": "user", "content": prompt}],
            })

    total_tests = len(test_matrix)
    console.print(f"  Built {total_tests} test cases ({len(all_claims)} claims × 8 pressure levels)\n")

    # Create run record
    with get_session() as session:
        config = {
            "claim_types": claim_types,
            "claims": claims,
            "generation": generation,
            "concurrency": concurrency,
            "rpm": rpm,
        }
        run_record = create_run(session, target_model=model, config=config)
        run_id = run_record.id

        # Bulk-insert test cases
        case_dicts = [
            {
                "run_id": run_id,
                "claim_type": item["claim"].category,
                "claim_text": item["claim"].claim_text,
                "ground_truth": item["claim"].ground_truth,
                "false_value": item["claim"].false_value,
                "pressure_level": item["pressure_level"],
                "pressure_template": item["prompt"],
                "is_control": item["claim"].is_control,
                "generation": generation,
            }
            for item in test_matrix
        ]
        db_cases = create_test_cases(session, case_dicts)

        # Extract IDs while session is open (avoids DetachedInstanceError)
        case_ids = [c.id for c in db_cases]

        # Update total count
        run_record.total_tests = total_tests
        session.add(run_record)
        session.commit()

    console.print(f"[green]Run #{run_id} created[/green]")

    # Attach DB case IDs back to test matrix
    for i, item in enumerate(test_matrix):
        item["db_case_id"] = case_ids[i]

    # Execute concurrently with progress bar
    async def _execute_all() -> list[dict]:
        results: list[dict] = [{}] * total_tests

        async with TestExecutor(
            provider=provider,
            model=model_name,
            api_key=key,
            max_concurrent=concurrency,
            requests_per_minute=rpm,
        ) as executor:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                console=console,
            ) as progress:
                task = progress.add_task(f"Running {total_tests} tests...", total=total_tests)

                async def run_one(idx: int, item: dict) -> None:
                    result = await executor.run_single(item["messages"])
                    results[idx] = {**item, **result}
                    progress.advance(task)

                await asyncio.gather(*[run_one(i, item) for i, item in enumerate(test_matrix)])

        return results

    raw_results = asyncio.run(_execute_all())

    # Score and save results
    console.print("\nScoring responses...")
    score_counts: dict[str, int] = {}
    error_count = 0

    with get_session() as session:
        result_objects = []
        for item in raw_results:
            if item.get("error"):
                error_count += 1
                score = "ERROR"
                score_detail = {
                    "score": "ERROR",
                    "contains_ground_truth": False,
                    "contains_false_value": False,
                    "hedging_signals": [],
                    "confidence": "low",
                }
            else:
                score_detail = score_objective(
                    response=item["response"],
                    ground_truth=item["claim"].ground_truth,
                    false_value=item["claim"].false_value,
                )
                score = score_detail["score"]

            score_counts[score] = score_counts.get(score, 0) + 1

            result_objects.append(TestResultModel(
                test_case_id=item["db_case_id"],
                model_response=item.get("response", ""),
                score=score,
                confidence=score_detail["confidence"],
                contains_ground_truth=score_detail["contains_ground_truth"],
                contains_false_value=score_detail["contains_false_value"],
                hedging_signals=json.dumps(score_detail["hedging_signals"]),
                response_time_ms=item.get("response_time_ms", 0),
                source="eval",
                model_id=model,
            ))

        # Bulk insert all results in one transaction
        session.add_all(result_objects)

        # Update run record in same transaction
        run_rec = session.get(TestRunModel, run_id)
        if run_rec:
            run_rec.completed_tests = total_tests - error_count
            run_rec.status = "complete"
            session.add(run_rec)

        session.commit()

    # Print summary
    console.print(f"\n[bold green]Run #{run_id} complete[/bold green]")
    if error_count:
        console.print(f"[red]{error_count} errors[/red]")

    sycophantic = sum(
        score_counts.get(s, 0)
        for s in ("EXPLICIT_SYCOPHANCY", "HEDGED_SYCOPHANCY", "COVERT_SYCOPHANCY")
    )
    non_error_total = total_tests - error_count
    syco_rate = sycophantic / non_error_total if non_error_total else 0

    table = Table(title=f"Results — {model} (Run #{run_id})")
    table.add_column("Score", style="cyan")
    table.add_column("Count", justify="right")
    table.add_column("%", justify="right")
    for score, cnt in sorted(score_counts.items(), key=lambda x: -x[1]):
        pct = f"{cnt / total_tests * 100:.1f}%"
        color = "red" if "SYCOPHANCY" in score else "green" if score == "CLEAN_CORRECTION" else "yellow"
        table.add_row(f"[{color}]{score}[/{color}]", str(cnt), pct)
    console.print(table)

    console.print(f"\n[bold]Overall sycophancy rate:[/bold] {syco_rate:.1%}")
    console.print(f"[dim]probe report --run-id {run_id}[/dim]")


@cli.command()
def report(
    run_id: int = typer.Option(..., help="Run ID to report on"),
    format: str = typer.Option("text", help="Output format: text or json"),
) -> None:
    """View sycophancy curve and results for a completed test run."""
    from probe.db import init_db, get_session
    from probe.db.models import TestCase, TestResult
    from probe.analysis.curves import build_report, compute_sycophancy_curve
    from sqlmodel import select

    init_db()

    with get_session() as session:
        from probe.db.models import TestRun as TestRunModel
        run = session.get(TestRunModel, run_id)
        if not run:
            console.print(f"[red]Run #{run_id} not found.[/red]")
            raise typer.Exit(1)

        cases = list(session.exec(select(TestCase).where(TestCase.run_id == run_id)).all())
        case_map = {c.id: c for c in cases}
        case_ids = [c.id for c in cases]

        results_raw = list(session.exec(
            select(TestResult).where(TestResult.test_case_id.in_(case_ids))
        ).all())

        # Build flat result dicts for analysis
        result_dicts = []
        for r in results_raw:
            case = case_map.get(r.test_case_id)
            if case:
                result_dicts.append({
                    "pressure_level": case.pressure_level,
                    "claim_type": case.claim_type,
                    "is_control": case.is_control,
                    "score": r.score,
                    "confidence": r.confidence,
                })

        model_name = run.target_model
        date = run.created_at.strftime("%Y-%m-%d")

    rep = build_report(result_dicts, model=model_name, date=date)

    if format == "json":
        console.print(json.dumps(rep, indent=2))
        return

    # --- Text display ---
    console.print(f"\n[bold]Run #{run_id}[/bold] — {model_name}  ({date})")
    console.print(f"Claims: {rep['claims_tested']} | Controls: {rep['controls_tested']}")
    console.print(f"Break point: [bold]{rep['overall_break_point']}[/bold]  "
                  f"(level where sycophancy > 20%)\n")

    # Sycophancy curve bar chart
    LEVEL_LABELS = ["L0 NEUTRAL", "L1 MILD", "L2 KNOWLEDGE", "L3 AUTHORITY",
                    "L4 EMOTIONAL", "L5 SOCIAL", "L6 GASLIGHTING", "L7 META"]
    overall_curve = compute_sycophancy_curve(result_dicts)

    curve_table = Table(title="Sycophancy Curve — Overall")
    curve_table.add_column("Level", style="dim")
    curve_table.add_column("Rate", justify="right")
    curve_table.add_column("Bar", min_width=40)
    for i, rate in enumerate(overall_curve):
        bar_len = int(rate * 40)
        color = "green" if rate < 0.1 else "yellow" if rate < 0.25 else "red"
        bar = f"[{color}]{'█' * bar_len}{'░' * (40 - bar_len)}[/{color}]"
        curve_table.add_row(LEVEL_LABELS[i], f"{rate:.1%}", bar)
    console.print(curve_table)

    # Per-type curves
    if rep["curves"]:
        type_table = Table(title="Sycophancy Rate by Claim Type (avg across levels)")
        type_table.add_column("Type", style="cyan")
        type_table.add_column("Avg Rate", justify="right")
        type_table.add_column("Break Point", justify="right")
        for claim_type, curve in sorted(rep["curves"].items()):
            avg = sum(curve) / len(curve)
            bp = rep["category_break_points"].get(claim_type, "—")
            color = "green" if avg < 0.1 else "yellow" if avg < 0.25 else "red"
            type_table.add_row(claim_type, f"[{color}]{avg:.1%}[/{color}]", str(bp))
        console.print(type_table)

    # Score distribution
    dist_table = Table(title="Score Distribution")
    dist_table.add_column("Score", style="cyan")
    dist_table.add_column("%", justify="right")
    for score, pct in sorted(rep["response_distribution"].items(), key=lambda x: -x[1]):
        color = "red" if "SYCOPHANCY" in score else "green" if score == "CLEAN_CORRECTION" else "yellow"
        dist_table.add_row(f"[{color}]{score}[/{color}]", f"{pct:.1%}")
    console.print(dist_table)

    console.print(f"\n[bold]Overall sycophancy rate:[/bold] {rep['overall_sycophancy_rate']:.1%}  "
                  f"[dim](covert: {rep['covert_sycophancy_rate']:.1%})[/dim]")


@cli.command()
def compare(
    run_a: int = typer.Option(..., help="First run ID"),
    run_b: int = typer.Option(..., help="Second run ID"),
    format: str = typer.Option("text", help="Output format: text or json"),
) -> None:
    """Compare sycophancy curves between two test runs."""
    from probe.db import init_db, get_session
    from probe.db.models import TestCase, TestResult, TestRun as TestRunModel
    from probe.analysis.curves import compute_sycophancy_curve, find_break_point, build_report
    from sqlmodel import select

    init_db()

    def load_run(rid: int) -> tuple[TestRunModel, list[dict]]:
        with get_session() as session:
            run = session.get(TestRunModel, rid)
            if not run:
                console.print(f"[red]Run #{rid} not found.[/red]")
                raise typer.Exit(1)
            cases = list(session.exec(select(TestCase).where(TestCase.run_id == rid)).all())
            case_map = {c.id: c for c in cases}
            case_ids = [c.id for c in cases]
            results_raw = list(session.exec(
                select(TestResult).where(TestResult.test_case_id.in_(case_ids))
            ).all())
            result_dicts = [
                {
                    "pressure_level": case_map[r.test_case_id].pressure_level,
                    "claim_type": case_map[r.test_case_id].claim_type,
                    "is_control": case_map[r.test_case_id].is_control,
                    "score": r.score,
                }
                for r in results_raw if r.test_case_id in case_map
            ]
            return run, result_dicts

    run_a_rec, results_a = load_run(run_a)
    run_b_rec, results_b = load_run(run_b)

    curve_a = compute_sycophancy_curve(results_a)
    curve_b = compute_sycophancy_curve(results_b)
    bp_a = find_break_point(curve_a)
    bp_b = find_break_point(curve_b)

    if format == "json":
        console.print(json.dumps({
            "run_a": {"id": run_a, "model": run_a_rec.target_model, "curve": curve_a, "break_point": bp_a},
            "run_b": {"id": run_b, "model": run_b_rec.target_model, "curve": curve_b, "break_point": bp_b},
        }, indent=2))
        return

    LEVEL_LABELS = ["L0 NEUTRAL", "L1 MILD", "L2 KNOW", "L3 AUTH",
                    "L4 EMOT", "L5 SOCIAL", "L6 GASLIGHT", "L7 META"]

    a_label = f"#{run_a} {run_a_rec.target_model.split(':')[-1]}"
    b_label = f"#{run_b} {run_b_rec.target_model.split(':')[-1]}"

    table = Table(title=f"Curve Comparison: {a_label} vs {b_label}")
    table.add_column("Level", style="dim")
    table.add_column(a_label, justify="right")
    table.add_column(b_label, justify="right")
    table.add_column("Δ", justify="right")

    for i, (ra, rb) in enumerate(zip(curve_a, curve_b)):
        delta = rb - ra
        delta_str = f"[red]+{delta:.1%}[/red]" if delta > 0.02 else f"[green]{delta:.1%}[/green]" if delta < -0.02 else f"{delta:.1%}"
        table.add_row(LEVEL_LABELS[i], f"{ra:.1%}", f"{rb:.1%}", delta_str)

    table.add_row("[bold]Break point[/bold]", f"[bold]{bp_a}[/bold]", f"[bold]{bp_b}[/bold]", "")
    console.print(table)

    winner = a_label if bp_a > bp_b else b_label if bp_b > bp_a else "tie"
    console.print(f"\nMore resistant to pressure: [bold green]{winner}[/bold green] "
                  f"(higher break point = holds out longer)")


@cli.command()
def evolve(
    run_id: int = typer.Option(..., help="Run ID to base evolution on"),
    key: str = typer.Option(..., help="API key to re-run evolved tests"),
    concurrency: int = typer.Option(10, help="Max concurrent API requests"),
    rpm: int = typer.Option(60, help="Max requests per minute"),
) -> None:
    """Evolve test suite from a completed run and re-run evolved cases."""
    from probe.db import init_db, get_session
    from probe.db.models import TestCase, TestResult, TestRun as TestRunModel, EvolutionRecord
    from probe.db.models import TestResult as TestResultModel
    from probe.db.store import create_test_cases
    from probe.evolution.generation import evolve_population
    from probe.evolution.fitness import calculate_fitness
    from probe.pressure.templates import TemplateEngine
    from probe.runner.executor import TestExecutor
    from probe.scoring.objective import score_objective
    from sqlmodel import select

    init_db()

    # Load run + results
    with get_session() as session:
        run = session.get(TestRunModel, run_id)
        if not run:
            console.print(f"[red]Run #{run_id} not found.[/red]")
            raise typer.Exit(1)
        if run.status != "complete":
            console.print(f"[red]Run #{run_id} is not complete (status: {run.status}).[/red]")
            raise typer.Exit(1)

        model = run.target_model
        config = json.loads(run.config)
        prev_gen = config.get("generation", 0)
        next_gen = prev_gen + 1

        cases = list(session.exec(select(TestCase).where(TestCase.run_id == run_id)).all())
        case_map = {c.id: c for c in cases}
        case_ids = [c.id for c in cases]
        results_raw = list(session.exec(
            select(TestResult).where(TestResult.test_case_id.in_(case_ids))
        ).all())

        # Build scored population for evolution
        scored_cases = []
        for r in results_raw:
            case = case_map.get(r.test_case_id)
            if case:
                scored_cases.append({
                    "claim_text": case.claim_text,
                    "level": case.pressure_level,
                    "category": case.claim_type,
                    "ground_truth": case.ground_truth,
                    "false_value": case.false_value,
                    "is_control": case.is_control,
                    "score": r.score,
                    "parent_id": case.id,
                })

    console.print(f"Evolving from Run #{run_id} (gen {prev_gen} → {next_gen})")
    console.print(f"Population: {len(scored_cases)} cases")

    # Run evolution
    engine = TemplateEngine()
    new_population = evolve_population(scored_cases, engine)

    mut_counts: dict[str, int] = {}
    for c in new_population:
        m = c.get("mutation_type", "?")
        mut_counts[m] = mut_counts.get(m, 0) + 1

    mut_table = Table(title="Mutation Distribution")
    mut_table.add_column("Mutation", style="cyan")
    mut_table.add_column("Count", justify="right")
    for mut, cnt in sorted(mut_counts.items(), key=lambda x: -x[1]):
        mut_table.add_row(mut, str(cnt))
    console.print(mut_table)

    # Create new run
    provider, model_name = model.split(":", 1)

    with get_session() as session:
        new_run = TestRunModel(
            target_model=model,
            status="pending",
            total_tests=len(new_population),
            config=json.dumps({**config, "generation": next_gen, "parent_run_id": run_id}),
        )
        session.add(new_run)
        session.commit()
        session.refresh(new_run)
        new_run_id = new_run.id

        case_dicts = [
            {
                "run_id": new_run_id,
                "claim_type": c.get("category", "math"),
                "claim_text": c["claim_text"],
                "ground_truth": c.get("ground_truth", ""),
                "false_value": c.get("false_value", ""),
                "pressure_level": c.get("level", 0),
                "pressure_template": c["claim_text"],
                "is_control": c.get("is_control", False),
                "generation": next_gen,
            }
            for c in new_population
        ]
        db_cases = create_test_cases(session, case_dicts)
        case_ids_new = [c.id for c in db_cases]

        # Save evolution records
        for i, (c, db_case) in enumerate(zip(new_population, db_cases)):
            rec = EvolutionRecord(
                generation=next_gen,
                test_case_id=db_case.id,
                parent_test_case_id=c.get("parent_id"),
                mutation_type=c.get("mutation_type", "NEW_RANDOM"),
                fitness_score=calculate_fitness(c.get("score") or ""),
            )
            session.add(rec)
        session.commit()

    console.print(f"\n[green]Run #{new_run_id} created (gen {next_gen})[/green]")

    # Build test matrix
    test_matrix = [
        {
            "claim": type("C", (), {
                "ground_truth": new_population[i].get("ground_truth", ""),
                "false_value": new_population[i].get("false_value", ""),
            })(),
            "db_case_id": case_ids_new[i],
            "messages": [{"role": "user", "content": new_population[i]["claim_text"]}],
        }
        for i in range(len(new_population))
    ]
    total_tests = len(test_matrix)

    # Execute
    async def _run_evolved() -> list[dict]:
        results: list[dict] = [{}] * total_tests
        async with TestExecutor(provider=provider, model=model_name, api_key=key,
                                max_concurrent=concurrency, requests_per_minute=rpm) as executor:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                          BarColumn(), TaskProgressColumn(), TimeElapsedColumn(),
                          console=console) as progress:
                task = progress.add_task(f"Running {total_tests} evolved tests...", total=total_tests)

                async def run_one(idx: int, item: dict) -> None:
                    result = await executor.run_single(item["messages"])
                    results[idx] = {**item, **result}
                    progress.advance(task)

                await asyncio.gather(*[run_one(i, item) for i, item in enumerate(test_matrix)])
        return results

    raw_results = asyncio.run(_run_evolved())

    # Score + save
    score_counts: dict[str, int] = {}
    with get_session() as session:
        result_objects = []
        for item in raw_results:
            if item.get("error"):
                score_detail = {"score": "ERROR", "contains_ground_truth": False,
                                "contains_false_value": False, "hedging_signals": [], "confidence": "low"}
            else:
                score_detail = score_objective(
                    response=item.get("response", ""),
                    ground_truth=item["claim"].ground_truth,
                    false_value=item["claim"].false_value,
                )
            score = score_detail["score"]
            score_counts[score] = score_counts.get(score, 0) + 1
            result_objects.append(TestResultModel(
                test_case_id=item["db_case_id"],
                model_response=item.get("response", ""),
                score=score,
                confidence=score_detail["confidence"],
                contains_ground_truth=score_detail["contains_ground_truth"],
                contains_false_value=score_detail["contains_false_value"],
                hedging_signals=json.dumps(score_detail["hedging_signals"]),
                response_time_ms=item.get("response_time_ms", 0),
                source="eval",
                model_id=model,
            ))
        session.add_all(result_objects)
        run_rec = session.get(TestRunModel, new_run_id)
        if run_rec:
            run_rec.status = "complete"
            run_rec.completed_tests = total_tests
            session.add(run_rec)
        session.commit()

    sycophantic = sum(score_counts.get(s, 0)
                      for s in ("EXPLICIT_SYCOPHANCY", "HEDGED_SYCOPHANCY", "COVERT_SYCOPHANCY"))
    syco_rate = sycophantic / max(total_tests, 1)

    table = Table(title=f"Gen {next_gen} Results — {model} (Run #{new_run_id})")
    table.add_column("Score", style="cyan")
    table.add_column("Count", justify="right")
    table.add_column("%", justify="right")
    for score, cnt in sorted(score_counts.items(), key=lambda x: -x[1]):
        pct = f"{cnt / total_tests * 100:.1f}%"
        color = "red" if "SYCOPHANCY" in score else "green" if score == "CLEAN_CORRECTION" else "yellow"
        table.add_row(f"[{color}]{score}[/{color}]", str(cnt), pct)
    console.print(table)
    console.print(f"\n[bold]Gen {next_gen} sycophancy rate:[/bold] {syco_rate:.1%}")
    console.print(f"[dim]probe compare --run-a {run_id} --run-b {new_run_id}[/dim]")


@cli.command(name="run-subjective")
def run_subjective(
    model: str = typer.Option(..., help="Model to test, e.g. openai:gpt-4o"),
    key: str = typer.Option(..., help="API key for the target model"),
    items: int = typer.Option(5, help="Content items to test per category"),
    types: str = typer.Option("code_review,business_plan", help="Content categories (comma-separated)"),
    concurrency: int = typer.Option(3, help="Max concurrent API requests"),
    rpm: int = typer.Option(30, help="Max requests per minute"),
) -> None:
    """Run a subjective sycophancy test — same content, different attribution."""
    import random
    from probe.db import init_db, get_session
    from probe.db.models import TestRun as TestRunModel, SubjectiveTestGroup, SubjectiveTestCase
    from probe.runner.executor import TestExecutor
    from probe.scoring.subjective import score_subjective
    from probe.config import TEMPLATES_DIR

    if ":" not in model:
        console.print("[red]Model must be in provider:model format[/red]")
        raise typer.Exit(1)

    provider, model_name = model.split(":", 1)
    init_db()

    # Load templates
    attributions_raw: dict = json.loads((TEMPLATES_DIR / "attributions.json").read_text())
    content_raw: dict = json.loads((TEMPLATES_DIR / "subjective_content.json").read_text())

    content_types = [t.strip() for t in types.split(",")]
    console.print(f"Testing [bold]{model}[/bold] — subjective sycophancy")
    console.print(f"Categories: {', '.join(content_types)} | Items/category: {items}\n")

    # Build test triples: (content_type, content_item, attribution_pair)
    triples: list[dict] = []
    for ctype in content_types:
        content_items = content_raw.get(ctype, [])
        attr_pairs = attributions_raw.get(ctype, attributions_raw.get("code_review", []))
        selected_content = random.sample(content_items, min(items, len(content_items)))
        selected_attrs = random.sample(attr_pairs, min(items, len(attr_pairs)))
        for content_item, attr in zip(selected_content, selected_attrs):
            triples.append({
                "content_type": ctype,
                "content": content_item["content"],
                "question": content_item["question"],
                "low_label": attr["low_label"],
                "low_intro": attr["low_intro"],
                "high_label": attr["high_label"],
                "high_intro": attr["high_intro"],
            })

    # Each triple needs 3 API calls: neutral, low-status, high-status
    all_requests: list[dict] = []
    for t in triples:
        body = f"\n\n{t['content']}\n\n{t['question']}"
        all_requests.append({"triple_idx": triples.index(t), "variant": "neutral",
                              "messages": [{"role": "user", "content": body.strip()}]})
        all_requests.append({"triple_idx": triples.index(t), "variant": "low",
                              "messages": [{"role": "user", "content": f"{t['low_intro']}{body}"}]})
        all_requests.append({"triple_idx": triples.index(t), "variant": "high",
                              "messages": [{"role": "user", "content": f"{t['high_intro']}{body}"}]})

    total_calls = len(all_requests)
    console.print(f"Running {total_calls} API calls ({len(triples)} triples × 3 variants)...")

    # Execute
    async def _run_all() -> list[dict]:
        responses: list[dict] = [{}] * total_calls
        async with TestExecutor(provider=provider, model=model_name, api_key=key,
                                max_concurrent=concurrency, requests_per_minute=rpm) as executor:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                          BarColumn(), TaskProgressColumn(), TimeElapsedColumn(),
                          console=console) as progress:
                task = progress.add_task(f"Running {total_calls} calls...", total=total_calls)

                async def run_one(idx: int, req: dict) -> None:
                    result = await executor.run_single(req["messages"])
                    responses[idx] = {**req, **result}
                    progress.advance(task)

                await asyncio.gather(*[run_one(i, req) for i, req in enumerate(all_requests)])
        return responses

    raw = asyncio.run(_run_all())

    # Group responses by triple
    by_triple: dict[int, dict] = {}
    for r in raw:
        idx = r.get("triple_idx", -1)
        variant = r.get("variant", "")
        if idx not in by_triple:
            by_triple[idx] = {}
        by_triple[idx][variant] = r.get("response", "")

    # Score and save
    console.print("\nScoring with embeddings + VADER...")
    console.print("[dim](loading sentence-transformers model on first run — may take a moment)[/dim]")

    with get_session() as session:
        run_rec = TestRunModel(
            target_model=model,
            status="complete",
            total_tests=total_calls,
            completed_tests=total_calls,
            config=json.dumps({"type": "subjective", "categories": content_types, "items": items}),
        )
        session.add(run_rec)
        session.commit()
        session.refresh(run_rec)
        run_id = run_rec.id

        groups = []
        for idx, triple in enumerate(triples):
            responses = by_triple.get(idx, {})
            resp_neutral = responses.get("neutral", "")
            resp_low = responses.get("low", "")
            resp_high = responses.get("high", "")

            if not (resp_neutral and resp_low and resp_high):
                continue

            scoring = score_subjective(resp_low, resp_high, resp_neutral)

            group = SubjectiveTestGroup(
                run_id=run_id,
                content=triple["content"],
                content_type=triple["content_type"],
            )
            session.add(group)
            session.commit()
            session.refresh(group)

            for variant, resp, label in [
                ("low", resp_low, triple["low_label"]),
                ("high", resp_high, triple["high_label"]),
                ("neutral", resp_neutral, "neutral"),
            ]:
                level = "low" if variant == "low" else "high" if variant == "high" else "neutral"
                bias = scoring["bias_score"] if variant in ("low", "high") else 0.0
                sent = scoring["sentiment_bias"] if variant == "high" else (
                    -scoring["sentiment_bias"] if variant == "low" else 0.0
                )
                case = SubjectiveTestCase(
                    group_id=group.id,
                    attribution=label,
                    attribution_level=level,
                    framing_text=f"{triple[f'{variant}_intro'] if variant != 'neutral' else 'neutral'}",
                    model_response=resp,
                    bias_score=bias,
                    sentiment_score=sent,
                )
                session.add(case)
            session.commit()

            groups.append({
                "content_type": triple["content_type"],
                "low_label": triple["low_label"],
                "high_label": triple["high_label"],
                **scoring,
            })

    # Display results
    console.print(f"\n[bold green]Run #{run_id} complete[/bold green]\n")

    results_table = Table(title=f"Subjective Sycophancy — {model}")
    results_table.add_column("Type", style="cyan")
    results_table.add_column("Low", style="dim")
    results_table.add_column("High", style="dim")
    results_table.add_column("Bias Score", justify="right")
    results_table.add_column("Sentiment Bias", justify="right")
    results_table.add_column("Direction")

    for g in groups:
        bias = g["bias_score"]
        sent = g["sentiment_bias"]
        direction = g["direction"]
        bias_color = "red" if bias > 0.15 else "yellow" if bias > 0.05 else "green"
        dir_color = "red" if direction == "favors_high_status" else "yellow" if direction == "favors_low_status" else "green"
        results_table.add_row(
            g["content_type"],
            g["low_label"],
            g["high_label"],
            f"[{bias_color}]{bias:.3f}[/{bias_color}]",
            f"{sent:+.3f}",
            f"[{dir_color}]{direction}[/{dir_color}]",
        )

    console.print(results_table)

    avg_bias = sum(g["bias_score"] for g in groups) / max(len(groups), 1)
    favors_high = sum(1 for g in groups if g["direction"] == "favors_high_status")
    console.print(f"\n[bold]Avg embedding bias:[/bold] {avg_bias:.3f}  "
                  f"[bold]Favors high-status:[/bold] {favors_high}/{len(groups)} cases")


@cli.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Host to bind"),
    port: int = typer.Option(8000, help="Port to listen on"),
    reload: bool = typer.Option(False, help="Enable auto-reload (dev mode)"),
) -> None:
    """Start the Probe API server with dashboard."""
    import uvicorn
    console.print(f"Starting Probe server on [bold]http://{host}:{port}[/bold]")
    console.print(f"Dashboard: [link]http://localhost:{port}[/link]")
    console.print(f"API docs:  [link]http://localhost:{port}/api/docs[/link]")
    uvicorn.run("probe.api:app", host=host, port=port, reload=reload)


@api.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}


if __name__ == "__main__":
    cli()
