"""
    test_iterutil
    ~~~~~~~~~~~~~

    Tests for the :mod:`~adbpy.iterutil` module.
"""

import pytest

from adbpy import iterutil


@pytest.fixture(scope='module', params=[
    list(),
    tuple(),
    set()
])
def iterables(request):
    """
    Fixture that yields objects that are iterables.
    """
    return request.param


@pytest.fixture(scope='module', params=[
    '',
    'foo',
    b'',
    b'foo',
    int(),
    float(),
    object()
])
def non_iterables(request):
    """
    Fixture that yields objects that are not iterables.
    """
    return request.param


@pytest.fixture(scope='function', params=[
    list(),
    tuple(),
    set()
])
def empty_iterable_funcs(request):
    """
    Fixture that yields iterables that are empty.
    """
    def func():
        return request.param
    return func


@pytest.fixture(scope='function', params=[
    ([1], 1),
    ([1, 2], 1),
    ((1,), 1),
    ((1, 2), 1),
    ({1}, 1),
    ({1, 2}, 1)
])
def non_empty_iterable_funcs(request):
    """
    Fixture that yields iterables that are not empty and the expected first item.
    """
    iterable, expected_first_item = request.param

    def func():
        return iterable

    return func, expected_first_item


def test_iterable_nop_on_iterable(iterables):
    """
    Assert that :func:`~adbpy.iterutil.iterable` returns the original input when given an iterable, excluding
    :class:`~str` and :class:`~bytes`.
    """
    assert iterutil.iterable(iterables) == iterables


def test_iterable_returns_list_of_input_on_non_iterable(non_iterables):
    """
    Assert that :func:`~adbpy.iterutil.iterable` returns a list of input items when given a non-iterable,
    :class:`~str`, or :class:`~bytes.`
    """
    assert iterutil.iterable(non_iterables)[0] == non_iterables


def test_first_raises_on_empty_iterable(empty_iterable_funcs):
    """
    Assert that :func:`~adbpy.iterutil.first` raises a :class:`~adbpy.iterutil.IterableEmpty` exception when
    given an iterable that yields no items.
    """
    with pytest.raises(iterutil.IterableEmpty):
        iterutil.first(empty_iterable_funcs)


def test_first_returns_first_item_on_non_empty_iterable(non_empty_iterable_funcs):
    """
    Assert that :func:`~adbpy.iterutil.first` returns the first item of the iterable when given an iterable
    that is not empty.
    """
    iterable, expected_first_item = non_empty_iterable_funcs
    assert iterutil.first(iterable) == expected_first_item
