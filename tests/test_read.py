"""Tests for the read operation."""
import io
import crudtoml

import pytest

from tests import redirect_stdin
import tests.test_data


def test_roundtrip(capsys):
    """Test that files aren't modified when round-tripping.

    When we do a read operation with no `path` parameter specified,
    the output should be identical to the input.
    """
    input_data = tests.TEST_DATA["example"]

    with redirect_stdin(io.StringIO(input_data)), pytest.raises(SystemExit, match="0"):
        crudtoml.main(["-", "read"])

    captured = capsys.readouterr()
    assert captured.out == input_data
    assert captured.err == ""
