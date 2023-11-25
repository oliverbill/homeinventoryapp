from http import HTTPStatus

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.timezone import now
from rest_framework.test import APIClient, APITestCase

from homeinventoryapi.models import InventoryItem, ShoppingListItem, ShoppingListItemStatus, InventoryItemStatus

USERNAME = 'alves.bill'
class ShoppingListItemE2ETest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username=USERNAME,
            password='12345'
        )
        self.client.force_authenticate(user=self.user)
        self.base_url = reverse('shoppinglistitem-list')
        self.shoppinglistitem_json = {
            'item_name': 'chocolate',
            'item_quantity': '3',
            'item_brand': 'Lindt',
            'item_grocery_store': 'ALDI',
            'expected_item_price_max': '4.12',
        }

    @pytest.mark.django_db
    def test_post(self):
        response = self.client.post(self.base_url, data=self.shoppinglistitem_json, format='json')
        self.assertEqual(response.status_code, HTTPStatus.CREATED._value_)
        saved_shoppinglistitem: ShoppingListItem = ShoppingListItem.objects.get()
        self.assertIsNotNone(saved_shoppinglistitem)
        self.assert_response_fields_equals_json_input(response, self.shoppinglistitem_json,
                                                      saved_shoppinglistitem.id)

    @pytest.mark.django_db
    def test_get(self):
        posted_shoppinglistitem = self.post_shoppinglistitem_and_getit_from_db()
        # get posted test data
        response = self.client.get(path=f'{self.base_url}{posted_shoppinglistitem.id}/', format='json')
        self.assert_response_fields_equals_json_input(response, self.shoppinglistitem_json,
                                                      posted_shoppinglistitem.id)

    @pytest.mark.django_db
    def test_patch(self):
        posted_item = self.post_shoppinglistitem_and_getit_from_db()
        response = self.client.patch(path=f'{self.base_url}{posted_item.id}/',
                                     data={'barcode': '668168168168',
                                           'payed_price': '5.64'},
                                     format='json')
        self.assertEqual(response.status_code, HTTPStatus.OK._value_)

    @pytest.mark.django_db
    def test_put(self):
        saved_shoppinglistitem = self.post_shoppinglistitem_and_getit_from_db()
        response = self.client.put(path=f'{self.base_url}{saved_shoppinglistitem.id}/',
                                   ## PUT tem q passar todos os fields, senao da HTTP 400:
                                            # campo c preenchimento obrigatorio
                                   data={
                                       'item_name': self.shoppinglistitem_json['item_name'],
                                       'item_quantity': self.shoppinglistitem_json['item_quantity'],
                                       'item_brand': 'Continente',
                                       'item_grocery_store': self.shoppinglistitem_json['item_grocery_store'],
                                       'expected_item_price_max': self.shoppinglistitem_json['expected_item_price_max']
                                   },
                                   format='json')

        self.assertEqual(response.status_code, HTTPStatus.OK._value_)
        self.assertEqual(response.data['item_brand'], 'Continente')

    @pytest.mark.django_db
    def post_shoppinglistitem_and_getit_from_db(self) -> InventoryItem:
        response = self.client.post(self.base_url, data=self.shoppinglistitem_json, format='json')
        self.assertEqual(response.status_code, HTTPStatus.CREATED._value_)
        created_datetime = response.data['created']
        self.assertIsNotNone(created_datetime)
        saved_shoppinglistitem: ShoppingListItem = ShoppingListItem.objects.filter(created=created_datetime).get()
        self.assertIsNotNone(saved_shoppinglistitem)

        return saved_shoppinglistitem

    def assert_response_fields_equals_json_input(self, response, json_input, shoppinglistitem_id):
        assert response.data['item_name'] == json_input['item_name']
        assert response.data['item_grocery_store'] == json_input['item_grocery_store']
        assert response.data['item_brand'] == json_input['item_brand']
        assert response.data['item_quantity'] == int(json_input['item_quantity'])
        assert response.data['expected_item_price_max'] == json_input['expected_item_price_max']
        assert response.data['status'] == ShoppingListItemStatus.CREATED._value_
        # calculated and auto fields
        self.assertIn(response.data['created'][0:9], str(now()))
        assert response.data['url'] == f'http://testserver/shoppinglistitem/{shoppinglistitem_id}/'

    def assert_inventory_item_is_stored(self, shoppinglistitem_json):
        shoplistitem = ShoppingListItem.objects.filter(created=shoppinglistitem_json['created']).get()
        created_inventory = InventoryItem.objects.filter(shoppinglistitem=shoplistitem).get()
        self.assertEqual(created_inventory.name, self.shoppinglistitem_json['item_name'])
        self.assertEqual(created_inventory.quantity, int(self.shoppinglistitem_json['item_quantity']))
        self.assertEqual(created_inventory.brand, self.shoppinglistitem_json['item_brand'])
        self.assertEqual(created_inventory.grocery_store, self.shoppinglistitem_json['item_grocery_store'])
        user = User.objects.get_by_natural_key(USERNAME)
        self.assertEqual(created_inventory.creator, user)
        assert created_inventory.status == InventoryItemStatus.STORED

