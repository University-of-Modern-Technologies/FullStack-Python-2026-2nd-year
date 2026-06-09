import unittest
from unittest.mock import patch, mock_open

from src.get_recipe.get_recipe import get_recipe

RECIPE_CSV = (
    "60b90c1c13067a15887e1ae1,Herbed Baked Salmon,4 lemons,1 large red onion,"
    "2 tablespoons chopped fresh basil\n"
    "60b90c2413067a15887e1ae2,Lemon Pancakes,2 tablespoons baking powder,"
    "1 cup vanilla-flavored almond milk,1 lemon\n"
)


class TestGetRecipe(unittest.TestCase):
    mock_open_file = None

    @classmethod
    def setUpClass(cls):
        cls.mock_open_file = mock_open(read_data=RECIPE_CSV)

    @classmethod
    def tearDownClass(cls):
        cls.mock_open_file = None

    def test_get_existing_recipe(self):
        filename = "fake.csv"
        search_id = "60b90c1c13067a15887e1ae1"

        with patch("builtins.open", self.mock_open_file):
            result = get_recipe(filename, search_id)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["id"], search_id)
        self.assertEqual(result["name"], "Herbed Baked Salmon")
        self.assertEqual(
            result["ingredients"],
            [
                "4 lemons",
                "1 large red onion",
                "2 tablespoons chopped fresh basil",
            ],
        )

    def test_get_existing_recipe_second_line(self):
        filename = "fake.csv"
        search_id = "60b90c2413067a15887e1ae2"

        with patch("builtins.open", self.mock_open_file):
            result = get_recipe(filename, search_id)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["id"], search_id)
        self.assertEqual(result["name"], "Lemon Pancakes")
        self.assertEqual(
            result["ingredients"],
            [
                "2 tablespoons baking powder",
                "1 cup vanilla-flavored almond milk",
                "1 lemon",
            ],
        )

    def test_get_non_existing_recipe(self):
        filename = "fake.csv"
        search_id = "non_existing_id"

        with patch("builtins.open", self.mock_open_file):
            result = get_recipe(filename, search_id)

        self.assertIsNone(result)

    def test_empty_file(self):
        filename = "fake.csv"
        empty_mock = mock_open(read_data="")

        with patch("builtins.open", empty_mock):
            result = get_recipe(filename, "any_id")

        self.assertIsNone(result)

    def test_invalid_file_format(self):
        filename = "fake.csv"
        invalid_mock = mock_open(read_data="invalid,format\n")

        with patch("builtins.open", invalid_mock):
            result = get_recipe(filename, "any_id")

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
