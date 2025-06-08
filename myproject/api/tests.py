from django.test import TestCase, Client
from .models import Item


class ItemsAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Если ваш API «смонтирован» на пути /api/,
        # можно добавить префикс: self.base = "/api/items"
        self.base = "/api/items"

    def test_create_and_get(self):
        # POST
        response = self.client.post(
            self.base,
            data={'name': 'Тест', 'price': 5.5},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        obj = response.json()
        self.assertEqual(obj['name'], 'Тест')

        # GET
        item_id = obj['id']
        response = self.client.get(f"{self.base}/{item_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['price'], 5.5)

    def test_404(self):
        response = self.client.get(f"{self.base}/999")
        self.assertEqual(response.status_code, 404)
