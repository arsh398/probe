"""Probe CLI and FastAPI app entry point."""

import json

import typer
from fastapi import FastAPI
from rich.console import Console
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
) -> None:
    """Run a sycophancy test against a target model."""
    console.print(f"[yellow]Run command not yet implemented (Week 2-3).[/yellow]")
    console.print(f"Would test [bold]{model}[/bold] with {claims} claims across {types}.")
    raise typer.Exit(1)


@cli.command()
def report(
    run_id: int = typer.Option(..., help="Run ID to report on"),
    format: str = typer.Option("text", help="Output format: text or json"),
) -> None:
    """View results for a completed test run."""
    console.print(f"[yellow]Report command not yet implemented (Week 4).[/yellow]")
    raise typer.Exit(1)


@cli.command()
def compare(
    run_a: int = typer.Option(..., help="First run ID"),
    run_b: int = typer.Option(..., help="Second run ID"),
) -> None:
    """Compare sycophancy curves between two test runs."""
    console.print(f"[yellow]Compare command not yet implemented (Week 4).[/yellow]")
    raise typer.Exit(1)


@cli.command()
def evolve(
    run_id: int = typer.Option(..., help="Run ID to evolve test cases from"),
) -> None:
    """Evolve the test suite based on results from a completed run."""
    console.print(f"[yellow]Evolve command not yet implemented (Week 4).[/yellow]")
    raise typer.Exit(1)


@cli.command(name="run-subjective")
def run_subjective(
    model: str = typer.Option(..., help="Model to test, e.g. openai:gpt-4o"),
    key: str = typer.Option(..., help="API key for the target model"),
) -> None:
    """Run a subjective sycophancy test (attribution-variant consistency)."""
    console.print(f"[yellow]Subjective run not yet implemented (Week 3).[/yellow]")
    raise typer.Exit(1)


@api.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}


if __name__ == "__main__":
    cli()
