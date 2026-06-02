"""05 — mock_open + кілька patch: I/O без реальних файлів, перевірка помилок."""
import unittest
from unittest.mock import patch, mock_open

from src.method.main import write_contacts_to_file, read_contacts_from_file


class TestContactsFileOperations(unittest.TestCase):
    def setUp(self):
        self.contacts = [
            {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "123-456-7890",
            },
            {
                "name": "Jane Smith",
                "email": "jane@example.com",
                "phone": "987-654-3210",
            },
        ]

    @patch('json.dump')
    @patch('builtins.open', new_callable=mock_open)
    def test_write_contacts(self, mock_file, mock_dump):
        write_contacts_to_file('contacts.json', self.contacts)

        mock_file.assert_called_with('contacts.json', 'w')
        mock_dump.assert_called_with({"contacts": self.contacts}, mock_file.return_value)
        self.assertEqual(mock_dump.call_count, 1)

    @patch('json.load')
    @patch('builtins.open', new_callable=mock_open)
    def test_read_contacts(self, mock_file, mock_load):
        mock_load.return_value = {"contacts": self.contacts}

        read_contacts = read_contacts_from_file('contacts.json')
        self.assertEqual(read_contacts, self.contacts)

        mock_file.assert_called_with('contacts.json', 'r')
        self.assertEqual(mock_load.call_count, 1)

    @patch('builtins.open', new_callable=mock_open)
    def test_write_contacts_file_error(self, mock_file):
        mock_file.side_effect = IOError("File not accessible")
        with self.assertRaises(IOError):
            write_contacts_to_file('contacts.json', self.contacts)

    @patch('builtins.open', new_callable=mock_open)
    def test_read_contacts_file_error_raises_io_error(self, mock_file):
        mock_file.side_effect = IOError("File not accessible")
        with self.assertRaises(IOError):
            read_contacts_from_file('contacts.json')


if __name__ == '__main__':
    unittest.main()
