from typing import List

from django.shortcuts import render, get_object_or_404
from ninja import NinjaAPI

from .schemas import ItemOut, ItemIn
from .models import Item

api = NinjaAPI()


@api.get("/hello")
def hello(request):
    """
    Просто hello... \n
    :param request: request \n
    :return: {"message": "Hello, world!"}
    """
    return {"message": "Hello, world!"}


# Эндпоинт для добавления элемента
@api.post("/items", response={201: ItemOut})
def create_item(request, data: ItemIn):
    """
    Для добавления предмета с именем и ценой \n
    :param request: request \n
    :param data: ItemIn \n
    :return: item
    """
    item = Item.objects.create(**data.dict())
    return 201, item


# Эндпоинт для получения одного предмета
@api.get("/items/{item_id}", response=ItemOut)
def get_item(request, item_id: int):
    """
    Получить один предмет по его ID.
    Если не найден, вернётся 404.
    """
    item = get_object_or_404(Item, pk=item_id)
    return item


# Эндпоинт для списка всех предметов
@api.get("/items", response=List[ItemOut])
def list_items(request):
    """
    Вернуть список всех предметов.
    """
    return Item.objects.all()
