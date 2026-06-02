"""03 — mock_open (read): читання CSV з оперативної пам'яті (пара до test_unittest_03_get_recipe.py)."""
from unittest.mock import patch, mock_open

from src.get_recipe.get_recipe import get_recipe

RECIPE_CSV = (
    "60b90c1c13067a15887e1ae1,Піца,томати,сир,базилік\n"
    "60b90c1c13067a15887e1ae2,Салат,огірки,томати,майонез\n"
    "60b90c1c13067a15887e1ae3,Суп,картопля,морква,цибуля\n"
)


@patch('builtins.open', new_callable=mock_open, read_data=RECIPE_CSV)
def test_get_existing_recipe(mock_file):
    result = get_recipe('fake.csv', "60b90c1c13067a15887e1ae1")

    assert result is not None
    assert result["id"] == "60b90c1c13067a15887e1ae1"
    assert result["name"] == "Піца"
    assert result["ingredients"] == ["томати", "сир", "базилік"]
    mock_file.assert_called_once_with('fake.csv', 'r')


@patch('builtins.open', new_callable=mock_open, read_data=RECIPE_CSV)
def test_get_non_existing_recipe(mock_file):
    result = get_recipe('fake.csv', "non_existing_id")

    assert result is None
    mock_file.assert_called_once_with('fake.csv', 'r')


@patch('builtins.open', new_callable=mock_open, read_data="")
def test_empty_file(mock_file):
    result = get_recipe('fake.csv', "any_id")

    assert result is None
    mock_file.assert_called_once_with('fake.csv', 'r')


@patch('builtins.open', new_callable=mock_open, read_data="invalid,format\n")
def test_invalid_file_format(mock_file):
    result = get_recipe('fake.csv', "any_id")

    assert result is None
    mock_file.assert_called_once_with('fake.csv', 'r')
