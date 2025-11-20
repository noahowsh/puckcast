"""Tests for data validation functionality."""

import json
from pathlib import Path

import pytest

# Test data directory
DATA_DIR = Path(__file__).parents[1] / "web" / "src" / "data"


class TestPredictionsValidation:
    """Test todaysPredictions.json validation."""

    def test_predictions_file_exists(self):
        """Test that predictions file exists."""
        predictions_file = DATA_DIR / "todaysPredictions.json"
        assert predictions_file.exists(), "todaysPredictions.json not found"

    def test_predictions_valid_json(self):
        """Test that predictions file is valid JSON."""
        predictions_file = DATA_DIR / "todaysPredictions.json"
        with open(predictions_file) as f:
            data = json.load(f)
        assert isinstance(data, dict), "Predictions must be a JSON object"

    def test_predictions_has_required_fields(self):
        """Test that predictions has required top-level fields."""
        predictions_file = DATA_DIR / "todaysPredictions.json"
        with open(predictions_file) as f:
            data = json.load(f)

        assert "generatedAt" in data, "Missing generatedAt field"
        assert "games" in data, "Missing games field"
        assert isinstance(data["games"], list), "games must be a list"

    def test_predictions_game_structure(self):
        """Test that each game has required fields."""
        predictions_file = DATA_DIR / "todaysPredictions.json"
        with open(predictions_file) as f:
            data = json.load(f)

        games = data.get("games", [])
        if not games:
            pytest.skip("No games in predictions file")

        required_fields = [
            "id",
            "gameDate",
            "homeTeam",
            "awayTeam",
            "homeWinProb",
            "awayWinProb",
            "confidenceGrade",
            "summary",
        ]

        for i, game in enumerate(games):
            for field in required_fields:
                assert (
                    field in game
                ), f"Game {i}: missing required field '{field}'"

    def test_predictions_probabilities_valid(self):
        """Test that probabilities are in valid range and sum to ~1."""
        predictions_file = DATA_DIR / "todaysPredictions.json"
        with open(predictions_file) as f:
            data = json.load(f)

        games = data.get("games", [])
        if not games:
            pytest.skip("No games in predictions file")

        for i, game in enumerate(games):
            home_prob = game.get("homeWinProb", 0)
            away_prob = game.get("awayWinProb", 0)

            # Check range
            assert (
                0 <= home_prob <= 1
            ), f"Game {i}: homeWinProb out of range [0,1]"
            assert (
                0 <= away_prob <= 1
            ), f"Game {i}: awayWinProb out of range [0,1]"

            # Check sum
            total_prob = home_prob + away_prob
            assert abs(total_prob - 1.0) < 0.01, f"Game {i}: probabilities sum to {total_prob}, expected ~1.0"

    def test_predictions_confidence_grades_valid(self):
        """Test that confidence grades are valid."""
        predictions_file = DATA_DIR / "todaysPredictions.json"
        with open(predictions_file) as f:
            data = json.load(f)

        games = data.get("games", [])
        if not games:
            pytest.skip("No games in predictions file")

        valid_grades = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C"]

        for i, game in enumerate(games):
            grade = game.get("confidenceGrade")
            assert (
                grade in valid_grades
            ), f"Game {i}: invalid confidence grade '{grade}'"


class TestModelInsightsValidation:
    """Test modelInsights.json validation."""

    def test_insights_file_exists(self):
        """Test that insights file exists."""
        insights_file = DATA_DIR / "modelInsights.json"
        if not insights_file.exists():
            pytest.skip("modelInsights.json not found (may not be generated yet)")

    def test_insights_valid_json(self):
        """Test that insights file is valid JSON."""
        insights_file = DATA_DIR / "modelInsights.json"
        if not insights_file.exists():
            pytest.skip("modelInsights.json not found")

        with open(insights_file) as f:
            data = json.load(f)
        assert isinstance(data, dict), "Insights must be a JSON object"

    def test_insights_has_required_fields(self):
        """Test that insights has required fields."""
        insights_file = DATA_DIR / "modelInsights.json"
        if not insights_file.exists():
            pytest.skip("modelInsights.json not found")

        with open(insights_file) as f:
            data = json.load(f)

        required_fields = ["generatedAt", "overall", "strategies", "confidenceBuckets"]

        for field in required_fields:
            assert field in data, f"Missing required field '{field}'"

    def test_insights_overall_metrics(self):
        """Test that overall metrics are present and valid."""
        insights_file = DATA_DIR / "modelInsights.json"
        if not insights_file.exists():
            pytest.skip("modelInsights.json not found")

        with open(insights_file) as f:
            data = json.load(f)

        overall = data.get("overall", {})
        assert "games" in overall, "overall missing 'games'"
        assert "accuracy" in overall, "overall missing 'accuracy'"
        assert "baseline" in overall, "overall missing 'baseline'"

        # Check accuracy is in valid range
        accuracy = overall.get("accuracy", 0)
        assert 0 <= accuracy <= 1, f"Accuracy out of range: {accuracy}"


class TestStandingsValidation:
    """Test currentStandings.json validation."""

    def test_standings_file_exists(self):
        """Test that standings file exists."""
        standings_file = DATA_DIR / "currentStandings.json"
        if not standings_file.exists():
            pytest.skip("currentStandings.json not found")

    def test_standings_valid_json(self):
        """Test that standings file is valid JSON."""
        standings_file = DATA_DIR / "currentStandings.json"
        if not standings_file.exists():
            pytest.skip("currentStandings.json not found")

        with open(standings_file) as f:
            data = json.load(f)
        assert isinstance(data, dict), "Standings must be a JSON object"

    def test_standings_has_teams(self):
        """Test that standings has teams list."""
        standings_file = DATA_DIR / "currentStandings.json"
        if not standings_file.exists():
            pytest.skip("currentStandings.json not found")

        with open(standings_file) as f:
            data = json.load(f)

        assert "teams" in data, "Missing 'teams' field"
        assert isinstance(data["teams"], list), "'teams' must be a list"


class TestGoaliePulseValidation:
    """Test goaliePulse.json validation."""

    def test_goalie_pulse_file_exists(self):
        """Test that goalie pulse file exists."""
        goalie_file = DATA_DIR / "goaliePulse.json"
        if not goalie_file.exists():
            pytest.skip("goaliePulse.json not found")

    def test_goalie_pulse_valid_json(self):
        """Test that goalie pulse file is valid JSON."""
        goalie_file = DATA_DIR / "goaliePulse.json"
        if not goalie_file.exists():
            pytest.skip("goaliePulse.json not found")

        with open(goalie_file) as f:
            data = json.load(f)
        assert isinstance(data, dict), "Goalie pulse must be a JSON object"

    def test_goalie_pulse_has_goalies(self):
        """Test that goalie pulse has goalies list."""
        goalie_file = DATA_DIR / "goaliePulse.json"
        if not goalie_file.exists():
            pytest.skip("goaliePulse.json not found")

        with open(goalie_file) as f:
            data = json.load(f)

        assert "goalies" in data, "Missing 'goalies' field"
        assert isinstance(data["goalies"], list), "'goalies' must be a list"

    def test_goalie_pulse_start_likelihood_valid(self):
        """Test that start likelihood is in valid range."""
        goalie_file = DATA_DIR / "goaliePulse.json"
        if not goalie_file.exists():
            pytest.skip("goaliePulse.json not found")

        with open(goalie_file) as f:
            data = json.load(f)

        goalies = data.get("goalies", [])
        if not goalies:
            pytest.skip("No goalies in file")

        for i, goalie in enumerate(goalies):
            likelihood = goalie.get("startLikelihood")
            if likelihood is not None:
                assert (
                    0 <= likelihood <= 1
                ), f"Goalie {i}: startLikelihood out of range [0,1]"
