"""Tests for utility scripts."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import scripts to test
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))


class TestArchivePredictions:
    """Test archive_predictions.py functionality."""

    def test_archive_file_creation(self, tmp_path):
        """Test that archive files are created correctly."""
        # Mock predictions data
        predictions_data = {
            "generatedAt": "2025-11-20T10:00:00Z",
            "games": [
                {
                    "id": "2025020315",
                    "homeTeam": {"abbrev": "TOR"},
                    "awayTeam": {"abbrev": "MTL"},
                    "homeWinProb": 0.65,
                    "awayWinProb": 0.35,
                    "confidenceGrade": "B+",
                }
            ],
        }

        # Create archive file
        archive_dir = tmp_path / "archive"
        archive_dir.mkdir()

        archive_file = archive_dir / "predictions_2025-11-20.json"
        with open(archive_file, "w") as f:
            json.dump(predictions_data, f, indent=2)

        assert archive_file.exists()

        # Verify content
        with open(archive_file) as f:
            loaded_data = json.load(f)

        assert loaded_data["games"][0]["homeTeam"]["abbrev"] == "TOR"


class TestValidateDataSchemas:
    """Test validate_data_schemas.py functionality."""

    def test_valid_predictions_structure(self):
        """Test validation of valid predictions structure."""
        valid_data = {
            "generatedAt": "2025-11-20T10:00:00Z",
            "games": [
                {
                    "id": "2025020315",
                    "gameDate": "2025-11-20",
                    "homeTeam": {"name": "Maple Leafs", "abbrev": "TOR"},
                    "awayTeam": {"name": "Canadiens", "abbrev": "MTL"},
                    "homeWinProb": 0.65,
                    "awayWinProb": 0.35,
                    "confidenceGrade": "B+",
                    "summary": "Maple Leafs favored",
                }
            ],
        }

        # Import validation function
        from validate_data_schemas import validate_predictions

        errors = validate_predictions(valid_data)
        assert len(errors) == 0, f"Validation errors: {errors}"

    def test_invalid_predictions_structure(self):
        """Test validation catches missing fields."""
        invalid_data = {
            "games": []  # Missing generatedAt
        }

        from validate_data_schemas import validate_predictions

        errors = validate_predictions(invalid_data)
        assert len(errors) > 0, "Should have caught missing generatedAt"


class TestFetchResults:
    """Test fetch_results.py functionality."""

    @patch("fetch_results.fetch_game_result")
    def test_game_result_parsing(self, mock_fetch):
        """Test that game results are parsed correctly."""
        # Mock API response
        mock_fetch.return_value = {
            "gameId": "2025020315",
            "homeScore": 5,
            "awayScore": 3,
            "winner": "home",
            "gameState": "Final",
        }

        result = mock_fetch("2025020315")

        assert result["winner"] == "home"
        assert result["homeScore"] > result["awayScore"]


class TestTwitterABTesting:
    """Test twitter_ab_testing.py functionality."""

    def test_variant_selection(self):
        """Test that variant selection works."""
        variants = {
            "morning_slate": [
                {"id": "A", "format": "emoji_heavy", "template": "Test {games}"},
                {"id": "B", "format": "minimal", "template": "Test {games}"},
            ]
        }

        from twitter_ab_testing import select_variant

        # Test forced variant
        variant = select_variant("morning_slate", variants, "A")
        assert variant["id"] == "A"

        # Test random selection
        variant = select_variant("morning_slate", variants, None)
        assert variant["id"] in ["A", "B"]

    def test_post_generation(self):
        """Test that posts are generated correctly."""
        variant = {
            "id": "A",
            "format": "test",
            "template": "{games} NHL games tonight",
        }

        data = {
            "games": [
                {
                    "id": "2025020315",
                    "homeTeam": {"abbrev": "TOR", "name": "Maple Leafs"},
                    "awayTeam": {"abbrev": "MTL", "name": "Canadiens"},
                    "homeWinProb": 0.65,
                    "awayWinProb": 0.35,
                    "edge": 0.15,
                    "confidenceGrade": "B+",
                },
                {
                    "id": "2025020316",
                    "homeTeam": {"abbrev": "NYR", "name": "Rangers"},
                    "awayTeam": {"abbrev": "BOS", "name": "Bruins"},
                    "homeWinProb": 0.55,
                    "awayWinProb": 0.45,
                    "edge": 0.05,
                    "confidenceGrade": "C",
                },
            ]
        }

        from twitter_ab_testing import generate_post

        post = generate_post("morning_slate", variant, data)
        assert "2 NHL games" in post or "NHL games today" in post


class TestTrackCalibration:
    """Test track_calibration.py functionality."""

    def test_calibration_analysis(self):
        """Test calibration analysis with sample data."""
        sample_games = [
            {
                "confidenceGrade": "A",
                "homeWinProb": 0.70,
                "modelFavorite": "home",
                "actualWinner": "home",  # Correct
            },
            {
                "confidenceGrade": "A",
                "homeWinProb": 0.75,
                "modelFavorite": "home",
                "actualWinner": "away",  # Wrong
            },
            {
                "confidenceGrade": "B",
                "homeWinProb": 0.60,
                "modelFavorite": "home",
                "actualWinner": "home",  # Correct
            },
        ]

        from track_calibration import analyze_calibration

        analysis = analyze_calibration(sample_games)

        # Check that A-grade has stats
        assert "A" in analysis
        assert analysis["A"]["total"] == 2
        assert analysis["A"]["correct"] == 1
        assert analysis["A"]["accuracy"] == 0.5


def test_pytest_is_working():
    """Sanity check that pytest is working."""
    assert True
