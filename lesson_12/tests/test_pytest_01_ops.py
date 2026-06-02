"""01 — pytest: функції, assert, pytest.raises, pytest.approx."""
import pytest

from src.example.ops import add, sub, mul, div


def test_add():
    assert add(2, 3) == 5


def test_sub():
    assert sub(2, 3) == -1


def test_mul():
    assert mul(2, 3) == 6


def test_div():
    assert div(2, 3) == pytest.approx(0.66666666)


def test_div_by_zero():
    with pytest.raises(ZeroDivisionError):
        div(3, 0)
