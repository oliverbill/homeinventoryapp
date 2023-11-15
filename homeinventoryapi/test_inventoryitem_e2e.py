import os
from http import HTTPStatus

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.timezone import now
from rest_framework.status import HTTP_403_FORBIDDEN
from rest_framework.test import APIClient, APITestCase

from homeinventoryapi.models import InventoryItem, ShoppingListItem
from utils import str_to_dict


class InventoryItemE2ETest(APITestCase):

    def setUp(self):
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homeinventoryapi.settings')
        self.client = APIClient()
        self.user = User.objects.create_superuser(
            username='admin',
            password='admin',
            email='admin@test.com'
        )
        self.client.force_authenticate(user=self.user)
        self.base_url = reverse('inventoryitem-list')
        self.shoppinglistitem_baseurl = reverse('shoppinglistitem-list')
        self.test_user_url = f'{reverse("user-list")}{self.user.id}/'
        self.user_json_response = self.client.get(path=self.test_user_url)
        assert self.user_json_response.status_code == HTTPStatus.OK
        self.inventoryitem_json = {
            'name': 'chocolate',
            'quantity': '3',
            'brand': 'Lindt',
            'grocery_store': 'ALDI',
            'payed_price': '4.12',
            'creator': self.user_json_response.data['url']
        }
        self.shoppinglistitem_json = {
            'item_name': 'chocolate',
            'item_quantity': '3',
            'item_brand': 'Lindt',
            'item_grocery_store': 'ALDI',
            'expected_item_price_max': '4.12',
            'buyer': self.user_json_response.data['url']
        }

    @pytest.mark.xfail(raises=HTTP_403_FORBIDDEN)
    def test_post_raises_405(self):
        self.client.post(path=self.base_url, data=self.inventoryitem_json)

    @pytest.mark.django_db
    def test_patch(self):
        saved_inventoryitem = self.post_shoppinglistitem_and_get_its_inventory_from_db()
        BARCODE = '98489462135135'
        response = self.client.patch(path=f'{self.base_url}{saved_inventoryitem.id}/', data={'barcode': BARCODE})
        assert response.status_code == 200
        queried_inv = InventoryItem.objects.get(pk=saved_inventoryitem.id)
        assert queried_inv.barcode == BARCODE

    @pytest.mark.django_db
    def test_get(self):
        saved_inventoryitem = self.post_shoppinglistitem_and_get_its_inventory_from_db()
        response = self.client.get(path=f'{self.base_url}{saved_inventoryitem.id}/')
        self.assertEqual(response.status_code, HTTPStatus.OK._value_)
        self.assert_response_fields_equals_json_input(response, self.inventoryitem_json, saved_inventoryitem)
        self.assertEqual(ShoppingListItem.objects.count(), 1)

    @pytest.mark.django_db
    def test_put(self):
        saved_inventoryitem = self.post_shoppinglistitem_and_get_its_inventory_from_db()
        updated_json = {
            'name': 'notebook',
            'quantity': '1',
            'brand': 'Dell',
            'grocery_store': 'CONTINENTE',
            'payed_price': '300.54',
            'creator': self.user_json_response.data['url']
        }
        response = self.client.put(path=f'{self.base_url}{saved_inventoryitem.id}/', data=updated_json)
        self.assert_response_fields_equals_json_input(response, updated_json, saved_inventoryitem)

    def assert_response_fields_equals_json_input(self, response, json_input, saved_inventoryitem):
        assert response.data['name'] == json_input['name']
        assert response.data['grocery_store'] == json_input['grocery_store']
        assert response.data['brand'] == json_input['brand']
        assert response.data['creator'] == json_input['creator']
        assert response.data['quantity'] == int(json_input['quantity'])
        # calculated and auto fields
        assert response.data['min_alert'] == 1

        assert response.data['shoppinglistitem'] == \
               f'http://testserver/shoppinglistitem/{saved_inventoryitem.shoppinglistitem.id}/'

        self.assertIn(response.data['created'][0:9], str(now()))
        assert response.data['stockout_at'] == None
        assert response.data['url'] == f'http://testserver/inventoryitem/{saved_inventoryitem.id}/'


    def post_shoppinglistitem_and_get_its_inventory_from_db(self) -> InventoryItem:
        # creates ShoppingListItem and InventoryItem
        response = self.client.post(self.shoppinglistitem_baseurl, data=self.shoppinglistitem_json, format='json')
        self.assertEqual(response.status_code, HTTPStatus.CREATED._value_)
        created_datetime = response.data['created']
        self.assertIsNotNone(created_datetime)
        saved_shoppinglistitem: ShoppingListItem = ShoppingListItem.objects.filter(created=created_datetime).get()
        self.assertIsNotNone(saved_shoppinglistitem)
        saved_inventoryitem = InventoryItem.objects.filter(shoppinglistitem=saved_shoppinglistitem).get()
        self.assertIsNotNone(saved_inventoryitem)
        return saved_inventoryitem
