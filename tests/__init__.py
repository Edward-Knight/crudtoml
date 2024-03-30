"""Tests for crudtoml."""
import contextlib
import io
import importlib.resources

import pytest

import crudtoml


class redirect_stdin(contextlib._RedirectStream):
    """Context manager for temporarily redirecting stdin to another file.

    Similar to contextlib.redirect_stdout.
    """

    _stream = "stdin"


def run(
    capsys, *args: str, input_data: str = "", exit_status: int = 0
) -> tuple[str, str]:
    """Shorthand for running crudtoml's main function.

    Redirects stdin and catches the SystemExit, returning a tuple of stdout and stderr.
    """
    with (
        redirect_stdin(io.StringIO(input_data)),
        pytest.raises(SystemExit, match=str(exit_status)),
    ):
        crudtoml.main(args)

    captured = capsys.readouterr()
    return captured.out, captured.err


# load test data from file on import
TEST_DATA: dict[str, str] = {}

for file in importlib.resources.files("tests.test_data").iterdir():
    if file.is_file() and file.name.endswith(".toml"):
        TEST_DATA[file.name.removesuffix(".toml")] = file.read_text()
