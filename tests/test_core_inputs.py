import pytest
import numpy as np
from behaviz.core.utils import validate_and_fix_inputs

# ---------------------------------------------------------------------
# Basic numeric list / tuple handling
# ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "inp, expected",
    [
        ([1, 2, 3], np.array([1, 2, 3])),
        ((1, 2, 3), np.array([1, 2, 3])),
        ([1.1, 2.2, 3.3], np.array([1.1, 2.2, 3.3])),
        ([1, 2.5, 3], np.array([1, 2.5, 3])),
    ],
)
def test_numeric_sequences_to_array(inp, expected):
    out = validate_and_fix_inputs(inp)

    assert isinstance(out, np.ndarray)
    np.testing.assert_array_equal(out, expected)


# ---------------------------------------------------------------------
# Nested sequences
# ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "inp",
    [
        [[1, 2], [3, 4]],
        ([1, 2], [3, 4]),
        ((1, 2), (3, 4)),
        [np.array([1, 2]), np.array([3, 4])],
    ],
)
def test_nested_sequences_to_list_of_arrays(inp):
    out = validate_and_fix_inputs(inp)

    assert isinstance(out, list)
    assert all(isinstance(x, np.ndarray) for x in out)

    np.testing.assert_array_equal(out[0], np.array([1, 2]))
    np.testing.assert_array_equal(out[1], np.array([3, 4]))


# ---------------------------------------------------------------------
# Existing ndarray input
# ---------------------------------------------------------------------


def test_ndarray_passthrough():
    arr = np.array([1, 2, 3])

    out = validate_and_fix_inputs(arr)

    assert out is arr


# ---------------------------------------------------------------------
# Multiple inputs
# ---------------------------------------------------------------------


def test_multiple_inputs_return_tuple():
    arr = np.array([4, 5, 6])

    out = validate_and_fix_inputs([1, 2, 3], arr)

    assert isinstance(out, tuple)
    assert len(out) == 2

    np.testing.assert_array_equal(out[0], np.array([1, 2, 3]))
    assert out[1] is arr


# ---------------------------------------------------------------------
# Empty inputs
# ---------------------------------------------------------------------


def test_empty_list_becomes_array():
    out = validate_and_fix_inputs([])

    assert isinstance(out, np.ndarray)
    assert out.size == 0


def test_empty_nested_list():
    out = validate_and_fix_inputs([[], []])

    assert isinstance(out, list)
    assert len(out) == 2

    for item in out:
        assert isinstance(item, np.ndarray)
        assert item.size == 0


# ---------------------------------------------------------------------
# Invalid / ignored inputs
# ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "inp",
    [
        "abc",
        123,
        3.14,
        {"a": 1},
        None,
    ],
)
def test_invalid_inputs_are_ignored(inp):
    with pytest.raises((TypeError, ValueError)):
        validate_and_fix_inputs(inp)


@pytest.mark.parametrize(
    "inp",
    [
        [1, "a", 3],
        [[1, 2], "abc"],
        [np.array([1]), 5],
    ],
)
def test_mixed_collections_raise_error(inp):
    with pytest.raises(ValueError):
        validate_and_fix_inputs(inp)


# ---------------------------------------------------------------------
# Mixed valid + invalid arguments
# ---------------------------------------------------------------------


def test_valid_and_invalid_arguments_together():
    out = validate_and_fix_inputs(
        [1, 2, 3],
        np.array([4, 5]),
    )

    assert isinstance(out, tuple)
    assert len(out) == 2

    np.testing.assert_array_equal(out[0], np.array([1, 2, 3]))
    np.testing.assert_array_equal(out[1], np.array([4, 5]))


# ---------------------------------------------------------------------
# Shape preservation
# ---------------------------------------------------------------------


def test_nested_arrays_keep_shapes():
    inp = [
        np.array([[1, 2], [3, 4]]),
        np.array([[5], [6]]),
    ]

    out = validate_and_fix_inputs(inp)

    assert out[0].shape == (2, 2)
    assert out[1].shape == (2, 1)


# ---------------------------------------------------------------------
# Single valid output should not be wrapped in tuple
# ---------------------------------------------------------------------


def test_single_output_not_tuple():
    out = validate_and_fix_inputs([1, 2, 3])

    assert not isinstance(out, tuple)
    assert isinstance(out, np.ndarray)
