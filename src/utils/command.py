"""Utility functions."""

import asyncio
import subprocess


async def run_command(
    command: str | list[str],
    cwd: str | None = None,
    timeout: int = 300,
) -> tuple[int, str, str]:
    """Run a shell command asynchronously.

    Args:
        command: Command to run (string or list of strings)
        cwd: Working directory
        timeout: Command timeout in seconds

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    if isinstance(command, str):
        # Shell command
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
        )
    else:
        # Command with arguments
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
        )

    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        return_code = process.returncode or 0
    except TimeoutError:
        process.kill()
        await process.wait()
        return 1, "", "Command timed out"

    return (
        return_code,
        stdout.decode("utf-8", errors="replace"),
        stderr.decode("utf-8", errors="replace"),
    )
