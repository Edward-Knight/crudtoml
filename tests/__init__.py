"""Tests for crudtoml."""
import contextlib
import importlib.resources


class redirect_stdin(contextlib._RedirectStream):
    """Context manager for temporarily redirecting stdin to another file.

    Similar to contextlib.redirect_stdout.
    """

    _stream = "stdin"


# load test data from file on import
TEST_DATA: dict[str, str] = {}

for file in importlib.resources.files("tests.test_data").iterdir():
    if file.is_file() and file.name.endswith(".toml"):
        TEST_DATA[file.name.removesuffix(".toml")] = file.read_text()
