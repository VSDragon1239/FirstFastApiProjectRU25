
import subprocess
import json

def run_curl(command: list) -> subprocess.CompletedProcess:
    """
    Функция запускает curl команду и возвращает CompletedProcess.
    """
    result = subprocess.run(command, capture_output=True, text=True)
    return result

def get_items():
    """
    GET /api/items
    """
    cmd = ["curl", "-s", "-X", "GET", "http://127.0.0.1:8000/api/items"]
    return run_curl(cmd)

def get_item(item_id: int):
    """
    GET /api/items/{item_id}
    """
    url = f"http://127.0.0.1:8000/api/items/{item_id}"
    cmd = ["curl", "-s", "-X", "GET", url]
    return run_curl(cmd)

def create_item(name: str, price: float):
    """
    POST /api/items
    """
    data = json.dumps({"name": name, "price": price})
    cmd = [
        "curl", "-s",
        "-X", "POST",
        "-H", "Content-Type: application/json",
        "-d", data,
        "http://127.0.0.1:8000/api/items"
    ]
    return run_curl(cmd)

def pretty_print(response: subprocess.CompletedProcess):
    """
    Парсит stdout как JSON и выводит красиво с кодировкой unicode.
    """
    try:
        obj = json.loads(response.stdout)
        print(json.dumps(obj, ensure_ascii=False, indent=2))
    except json.JSONDecodeError:
        # Если ответ не JSON, печатаем как есть
        print(response.stdout)

if __name__ == "__main__":
    print("Список предметов:")
    res = get_items()
    pretty_print(res)

    # print("\nСоздаем новый предмет:")
    # res = create_item("Новый предмет", 25.5)
    # pretty_print(res)

    print("\nПолучаем предмет с ID=1:")
    res = get_item(1)
    pretty_print(res)