"""Command-line interface to train and evaluate NHL game prediction model."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

import typer
from rich.console import Console
from .pipeline import Dataset, build_dataset
from .model import (
    compute_metrics,
    create_baseline_model,
    fit_model,
    format_metrics,
    predict_probabilities,
)

app = typer.Typer(add_completion=False)
console = Console()


def _resolve_seasons(train_seasons: List[str] | None, test_season: str | None) -> tuple[List[str], str]:
    default_train = ["20212022", "20222023"]
    default_test = "20232024"
    train = train_seasons or default_train
    test = test_season or default_test
    if test in train:
        raise typer.BadParameter("Test season must be distinct from training seasons.")
    return train, test


@app.command()
def train(
    train_seasons: List[str] = typer.Option(None, help="Season IDs for training data."),
    test_season: str = typer.Option(None, help="Hold-out season ID for evaluation."),
) -> None:
    """Train the logistic regression baseline and print evaluation metrics."""
    train_ids, test_id = _resolve_seasons(train_seasons, test_season)
    combined_seasons = sorted(set(train_ids + [test_id]))

    console.log(f"Fetching data for seasons: {', '.join(combined_seasons)}")
    dataset: Dataset = build_dataset(combined_seasons)

    games = dataset.games
    features = dataset.features
    target = dataset.target

    train_mask = games["seasonId"].isin(train_ids)
    test_mask = games["seasonId"] == test_id

    if train_mask.sum() == 0 or test_mask.sum() == 0:
        raise typer.BadParameter("Insufficient games for the provided seasons.")

    model = create_baseline_model()
    model = fit_model(model, features, target, train_mask)

    train_probs = predict_probabilities(model, features, train_mask)
    test_probs = predict_probabilities(model, features, test_mask)

    train_metrics = compute_metrics(target.loc[train_mask], train_probs)
    test_metrics = compute_metrics(target.loc[test_mask], test_probs)

    console.print("[bold]Training Metrics[/bold]")
    console.print(format_metrics("Train", train_metrics))

    console.print("\n[bold]Test Metrics[/bold]")
    console.print(format_metrics("Test", test_metrics))

    baseline = max(target.loc[test_mask].mean(), 1 - target.loc[test_mask].mean())
    console.print(f"\nBaseline Accuracy (Most Frequent Class): {baseline:0.4f}")


if __name__ == "__main__":
    app()
