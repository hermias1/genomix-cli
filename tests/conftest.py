"""Shared test fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def tmp_project(tmp_path):
    """Create a temporary project directory."""
    return tmp_path


@pytest.fixture
def fixtures_dir():
    """Path to test fixtures."""
    return Path(__file__).parent / "fixtures"
