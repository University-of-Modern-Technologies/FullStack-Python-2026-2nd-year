"""04 — @patch: реальний підрахунок, mock reduce, side_effect (своя функція)."""
import unittest
from unittest.mock import patch

from src.reduce_sum.answer import reduce, sum_numbers


def fake_reduce(func, numbers):
    """Підміна reduce у тесті — рахує через func, як справжній reduce."""
    result = numbers[0]
    for n in numbers[1:]:
        result = func(result, n)
    return result


class TestSumNumbers(unittest.TestCase):
    @patch('src.reduce_sum.answer.other')
    def test_sum_real_calculation(self, mock_other):
        """Чесна перевірка: reduce рахує, other() не друкує в консоль."""
        numbers = [1, 14, 6, 19, 34, 22]

        result = sum_numbers(numbers)

        self.assertEqual(result, 96)
        mock_other.assert_called_once()

    @patch('src.reduce_sum.answer.reduce', wraps=reduce)
    def test_sum_mock_reduce(self, mock_reduce):
        """wraps=reduce: spy — reduce рахує, mock фіксує виклик і call_args."""
        numbers = [1, 14, 6, 19, 34, 22]

        result = sum_numbers(numbers)

        self.assertEqual(result, 96)
        mock_reduce.assert_called_once()

        # call_args — (args, kwargs) останнього виклику mock_reduce(...)
        # У коді: reduce(lambda x, y: x + y, numbers)
        #   args[0] — lambda
        #   args[1] — numbers
        args, _ = mock_reduce.call_args
        self.assertEqual(args[1], numbers)
        self.assertTrue(callable(args[0]))
        self.assertEqual(args[0](1, 2), 3)

    @patch('src.reduce_sum.answer.other')
    @patch('src.reduce_sum.answer.reduce', side_effect=fake_reduce)
    def test_sum_fake_reduce(self, mock_reduce, mock_other):
        """side_effect: замість return_value підставляємо свою функцію — вона виконується."""
        numbers = [1, 14, 6, 19, 34, 22]

        result = sum_numbers(numbers)

        self.assertEqual(result, 96)
        mock_other.assert_called_once()
        mock_reduce.assert_called_once()


if __name__ == '__main__':
    unittest.main()
