"""Tests for the read operation."""
from tests import run
import tests.test_data


def test_roundtrip(capsys):
    """Test that files aren't modified when round-tripping.

    When we do a read operation with no `path` parameter specified,
    the output should be identical to the input.
    """
    input_data = tests.TEST_DATA["example"]

    assert run(capsys, "-", "read", input_data=input_data) == (input_data, "")
