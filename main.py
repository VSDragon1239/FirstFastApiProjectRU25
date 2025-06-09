# Создание файла curl_requests.py с функциями, вызывающими curl через subprocess

code = """
import subprocess
import json

def run_curl(command: list) -> subprocess.CompletedProcess:
    \"""
    Функция запускает curl команду и возвращает CompletedProcess.
    \"""
    result = subprocess.run(command, capture_output=True, text=True)
    return result

def get_items():
    \"""
    GET /api/items
    \"""
    cmd = ["curl", "-s", "-X", "GET", "http://127.0.0.1:8000/api/items"]
    return run_curl(cmd)

def get_item(item_id: int):
    \"""
    GET /api/items/{item_id}
    \"""
    url = f"http://127.0.0.1:8000/api/items/{item_id}"
    cmd = ["curl", "-s", "-X", "GET", url]
    return run_curl(cmd)

def create_item(name: str, price: float):
    \"""
    POST /api/items
    \"""
    data = json.dumps({"name": name, "price": price})
    cmd = [
        "curl", "-s",
        "-X", "POST",
        "-H", "Content-Type: application/json",
        "-d", data,
        "http://127.0.0.1:8000/api/items"
    ]
    return run_curl(cmd)

if __name__ == "__main__":
    # Пример использования
    print("Список предметов:")
    res = get_items()
    print(res.stdout)

    print("Создаем новый предмет:")
    res = create_item("Sample Item", 15.99)
    print(res.stdout)

    print("Получаем предмет с ID=1:")
    res = get_item(1)
    print(res.stdout)
"""

# Сохраняем файл
file_path = "curl_requests.py"
with open(file_path, "w", encoding="utf-8") as f:
    f.write(code)

file_path
