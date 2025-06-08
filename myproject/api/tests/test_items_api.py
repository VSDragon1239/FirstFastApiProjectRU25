import pytest
from ninja.testing import TestClient

from api.views import api             # ваш NinjaAPI-объект
from api.models import Item
from django.urls import reverse

client = TestClient(api)


@pytest.mark.django_db
def test_create_item():
    # Подготовка: в БД нет ни одного предмета
    assert Item.objects.count() == 0

    # Выполняем POST /items
    payload = {"name": "Тестовый", "price": 123.45}
    response = client.post("/items", json=payload)

    # Проверяем HTTP-статус и содержание
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Тестовый"
    assert data["price"] == 123.45

    # И в базе появился один объект
    assert Item.objects.count() == 1


@pytest.mark.django_db
def test_get_item():
    # Создаём объект прямо в БД
    item = Item.objects.create(name="Alpha", price=10.0)

    # GET по существующему ID
    response = client.get(f"/items/{item.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Alpha"
    assert data["price"] == 10.0

    # GET по несуществующему ID возвращает 404
    response_404 = client.get("/items/9999")
    assert response_404.status_code == 404


@pytest.mark.django_db
def test_list_items():
    # Добавляем несколько предметов
    Item.objects.create(name="A", price=1)
    Item.objects.create(name="B", price=2)

    response = client.get("/items")
    assert response.status_code == 200

    data = response.json()
    # Ожидаем список из двух элементов
    assert isinstance(data, list)
    names = [item["name"] for item in data]
    assert "A" in names and "B" in names
