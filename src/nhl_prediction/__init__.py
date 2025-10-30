"""NHL game prediction pipeline."""

from importlib.metadata import version, PackageNotFoundError


def get_version() -> str:
    """Return installed package version or '0.0.0' if not installed."""
    try:
        return version("nhl_prediction")
    except PackageNotFoundError:  # package is not installed in editable mode
        return "0.0.0"


__all__ = ["get_version"]
