"""02 — pytest для OOP: наслідування, MRO (пара до test_unittest_02_animal.py)."""
from src.my_class.main import Animal, Cat, Dog, CatDog, DogCat


def test_animal_creation():
    animal = Animal("Test", 10)
    assert animal.nickname == "Test"
    assert animal.weight == 10
    assert animal.say() is None


def test_cat_creation():
    cat = Cat("Murzik", 5)
    assert cat.nickname == "Murzik"
    assert cat.weight == 5
    assert cat.say() == "Meow"


def test_dog_creation():
    dog = Dog("Rex", 15)
    assert dog.nickname == "Rex"
    assert dog.weight == 15
    assert dog.say() == "Woof"


def test_catdog_creation():
    catdog = CatDog("Mix", 8)
    assert catdog.nickname == "Mix"
    assert catdog.weight == 8
    assert catdog.say() == "Meow"
    assert catdog.info() == "Mix-8"


def test_dogcat_creation():
    dogcat = DogCat("Mix", 8)
    assert dogcat.nickname == "Mix"
    assert dogcat.weight == 8
    assert dogcat.say() == "Woof"
    assert dogcat.info() == "Mix-8"


def test_mro_order():
    catdog = CatDog("Mix", 8)
    dogcat = DogCat("Mix", 8)
    assert catdog.say() == "Meow"
    assert dogcat.say() == "Woof"
