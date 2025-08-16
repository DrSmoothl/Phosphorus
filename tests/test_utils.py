"""Tests for utility functions."""

import pytest

from src.utils import run_command


@pytest.mark.asyncio
async def test_run_command_success():
    """Test successful command execution."""
    # Test a simple command that should work on both Windows and Unix
    return_code, stdout, stderr = await run_command("echo hello")

    assert return_code == 0
    assert "hello" in stdout.strip()
    assert stderr == ""


@pytest.mark.asyncio
async def test_run_command_failure():
    """Test failed command execution."""
    # This command should fail
    return_code, stdout, stderr = await run_command("nonexistent_command_xyz")

    assert return_code != 0
    assert stderr != ""
