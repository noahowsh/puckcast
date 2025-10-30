"""Shared modelling utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def create_baseline_model(random_state: int | None = 42) -> Pipeline:
    """Return the logistic regression baseline pipeline."""
    return Pipeline(
        steps=[
            ("scale", StandardScaler()),
            ("clf", LogisticRegression(max_iter=2000, solver="lbfgs", random_state=random_state)),
        ]
    )


def fit_model(model: Pipeline, features: pd.DataFrame, target: pd.Series, mask: pd.Series) -> Pipeline:
    """Fit the provided model on masked rows."""
    model.fit(features.loc[mask], target.loc[mask])
    return model


def predict_probabilities(model: Pipeline, features: pd.DataFrame, mask: pd.Series) -> np.ndarray:
    """Return probability of home win for masked rows."""
    return model.predict_proba(features.loc[mask])[:, 1]


def compute_metrics(y_true: pd.Series, y_prob: np.ndarray) -> Dict[str, float]:
    """Compute standard evaluation metrics."""
    y_pred = (y_prob >= 0.5).astype(int)
    metrics = {
        "accuracy": accuracy_score(y_true, y_pred),
        "log_loss": log_loss(y_true, y_prob),
        "brier_score": brier_score_loss(y_true, y_prob),
        "roc_auc": roc_auc_score(y_true, y_prob),
    }
    return metrics


def format_metrics(prefix: str, metrics: Dict[str, float]) -> str:
    """Format metrics into a printable string."""
    parts = [f"{prefix}"]
    parts.extend(f"{key.replace('_', ' ').title()}: {value:0.4f}" for key, value in metrics.items())
    return " | ".join(parts)


def compute_feature_effects(model: Pipeline, feature_names: pd.Index) -> pd.DataFrame:
    """Return coefficient impacts in original feature scale."""
    scaler: StandardScaler = model.named_steps["scale"]
    clf: LogisticRegression = model.named_steps["clf"]

    coef = clf.coef_[0]
    # Undo standardisation: divide by scale; handle zero scale defensively.
    scale = np.where(scaler.scale_ == 0, 1.0, scaler.scale_)
    adjusted_coef = coef / scale

    importance = pd.DataFrame(
        {"feature": feature_names, "coefficient": adjusted_coef, "absolute_importance": np.abs(adjusted_coef)}
    ).sort_values("absolute_importance", ascending=False)
    return importance


__all__ = [
    "create_baseline_model",
    "fit_model",
    "predict_probabilities",
    "compute_metrics",
    "format_metrics",
    "compute_feature_effects",
]
