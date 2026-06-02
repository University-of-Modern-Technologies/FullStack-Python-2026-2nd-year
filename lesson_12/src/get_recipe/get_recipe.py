def get_recipe(path, search_id):
    result = None
    with open(path, "r") as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) < 2:  # Перевірка на мінімальну кількість полів
                continue
            id = parts[0]
            name = parts[1]
            recipes = parts[2:] if len(parts) > 2 else []
            if id == search_id:
                result = {"id": id, "name": name, "ingredients": recipes}
                break
    return result


if __name__ == '__main__':
    result = get_recipe('ingredients.csv', "60b90c1c13067a15887e1ae1")
    print(result)
