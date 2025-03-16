"""Test cases for Komfovent helper functions."""

import pytest

from custom_components.komfovent.helpers import get_version_from_int


def test_get_version_from_int():
    """Test version number extraction from packed integer."""
    # Test the example case from the docstring
    assert get_version_from_int(18886660) == (1, 2, 3, 4)

    # Test some additional cases
    assert get_version_from_int(0) == (0, 0, 0, 0)
    assert get_version_from_int(0xFFFFFFFF) == (255, 15, 255, 4095)
