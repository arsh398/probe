"""
Benchmark script — run Probe against multiple models and generate a comparison report.
Used to produce the marketing benchmark report.

Usage:
    python scripts/run_benchmark.py --config benchmark_config.json
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

import typer

app = typer.Typer()


@app.command()
def main(
    config: str = typer.Option("benchmark_config.json", help="Path to benchmark config JSON"),
    output: str = typer.Option("benchmark_report.json", help="Output report path"),
) -> None:
    """Run sycophancy benchmark across multiple models. (Implemented in Week 5)"""
    typer.echo("[yellow]Benchmark runner not yet implemented (Week 5).[/yellow]")
    typer.echo("")
    typer.echo("Expected config format:")
    example = {
        "models": [
            {"provider": "openai", "model": "gpt-4o", "api_key": "sk-xxx"},
            {"provider": "anthropic", "model": "claude-sonnet-4-6", "api_key": "sk-ant-xxx"},
        ],
        "claims_per_model": 500,
        "claim_types": ["math", "logic", "science", "code"],
    }
    typer.echo(json.dumps(example, indent=2))
    raise typer.Exit(1)


if __name__ == "__main__":
    app()
