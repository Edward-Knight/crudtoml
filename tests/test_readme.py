"""Test the examples in the project readme work as expected."""
import textwrap

from tests import run
import tests.test_data


def test_example_create(capsys):
    """Test the "create" example in the readme."""
    input_data = tests.TEST_DATA["test"]
    output_data = textwrap.dedent(
        """
        [project]
        name = "crudtoml"
        dob = 2023-05-23
        """
    ).lstrip()

    out, err = run(
        capsys, "-", "create", "project", "dob", "2023-05-23", input_data=input_data
    )

    assert out == output_data
    assert err == ""


def test_example_read(capsys):
    """Test the "read" example in the readme."""
    input_data = tests.TEST_DATA["test"]

    out, err = run(capsys, "-", "read", "project", "name", input_data=input_data)

    assert out == '"crudtoml"'
    assert err == ""


def test_example_update(capsys):
    """Test the "update" example in the readme."""
    input_data = tests.TEST_DATA["test"]
    output_data = textwrap.dedent(
        """
        [project]
        name = "crudini"
        """
    ).lstrip()

    out, err = run(
        capsys, "-", "update", "project", "name", '"crudini"', input_data=input_data
    )

    assert out == output_data
    assert err == ""


def test_example_delete(capsys):
    """Test the "delete" example in the readme."""
    input_data = tests.TEST_DATA["test"]

    out, err = run(capsys, "-", "delete", "project", "name", input_data=input_data)

    assert out == "[project]\n"
    assert err == ""
