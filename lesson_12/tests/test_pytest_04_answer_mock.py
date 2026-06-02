"""04 — @patch у pytest (пара до test_unittest_04_answer_mock.py)."""
from unittest.mock import patch

from src.reduce_sum.answer import reduce, sum_numbers


def fake_reduce(func, numbers):
    result = numbers[0]
    for n in numbers[1:]:
        result = func(result, n)
    return result


@patch("src.reduce_sum.answer.other")
def test_sum_real_calculation(mock_other):
    numbers = [1, 14, 6, 19, 34, 22]

    result = sum_numbers(numbers)

    assert result == 96
    mock_other.assert_called_once()


@patch("src.reduce_sum.answer.reduce", wraps=reduce)
def test_sum_mock_reduce(mock_reduce):
    numbers = [1, 14, 6, 19, 34, 22]

    result = sum_numbers(numbers)

    assert result == 96
    mock_reduce.assert_called_once()
    args, _ = mock_reduce.call_args
    assert args[1] == numbers
    assert callable(args[0])
    assert args[0](1, 2) == 3


@patch("src.reduce_sum.answer.other")
@patch("src.reduce_sum.answer.reduce", side_effect=fake_reduce)
def test_sum_fake_reduce(mock_reduce, mock_other):
    numbers = [1, 14, 6, 19, 34, 22]

    result = sum_numbers(numbers)

    assert result == 96
    mock_other.assert_called_once()
    mock_reduce.assert_called_once()
