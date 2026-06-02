"""06 — mock_open: запис CSV абітурієнтів (src/save_data/answer.py)."""
import unittest
from unittest.mock import patch, mock_open, call

from src.save_data.answer import applicant, save_applicant_data


class TestSaveApplicantData(unittest.TestCase):
    @patch('builtins.open', new_callable=mock_open)
    def test_open_file(self, mock_file):
        save_applicant_data(applicant, 'fake.csv')

        self.assertEqual(mock_file.call_count, 1, msg='Function open only one call')
        print("\n", mock_file.call_args[0])
        print(mock_file.call_args[1])
        mock_file.assert_called()
        mock_file.assert_called_with('fake.csv', 'w', encoding='utf-8')

    @patch('builtins.open', new_callable=mock_open)
    def test_write_file(self, mock_file):
        save_applicant_data(applicant, 'fake.csv')

        expected_calls = [
            call('Kovalchuk Oleksiy,301,175,180,155\n'),
            call('Ivanchuk Boryslav,101,135,150,165\n'),
            call('Karpenko Dmitro,201,155,175,185\n'),
        ]
        mock_file().write.assert_has_calls(expected_calls, any_order=True)


if __name__ == '__main__':
    unittest.main()
