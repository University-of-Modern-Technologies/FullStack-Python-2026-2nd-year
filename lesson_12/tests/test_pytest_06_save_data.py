"""06 — mock_open: запис CSV абітурієнтів (пара до test_unittest_06_save_data.py)."""
from unittest.mock import patch, mock_open, call

from src.save_data.answer import applicant, save_applicant_data


@patch('builtins.open', new_callable=mock_open)
def test_open_file(mock_file):
    save_applicant_data(applicant, 'fake.csv')

    assert mock_file.call_count == 1
    mock_file.assert_called_with('fake.csv', 'w', encoding='utf-8')


@patch('builtins.open', new_callable=mock_open)
def test_write_file(mock_file):
    save_applicant_data(applicant, 'fake.csv')

    expected_calls = [
        call('Kovalchuk Oleksiy,301,175,180,155\n'),
        call('Ivanchuk Boryslav,101,135,150,165\n'),
        call('Karpenko Dmitro,201,155,175,185\n'),
    ]
    mock_file().write.assert_has_calls(expected_calls, any_order=True)
