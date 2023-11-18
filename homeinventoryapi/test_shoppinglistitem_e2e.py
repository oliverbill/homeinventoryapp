from http import HTTPStatus

import pytest
from _decimal import Decimal
from django.contrib.auth.models import User
from django.template.defaulttags import now
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from homeinventoryapi.models import InventoryItem, ShoppingListItem, ShoppingListItemStatus


class ShoppingListItemE2ETest(APITestCase):

    def setUp(self):
        # os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homeinventoryapi.settings')
        self.client = APIClient()
        self.user = User.objects.create_superuser(
            username='admin',
            password='admin',
            email='admin@test.com'
        )
        self.client.force_authenticate(user=self.user)
        self.base_url = reverse('shoppinglistitem-list')
        self.test_user_url = f'{reverse("user-list")}{self.user.id}/'
        self.user_json_response = self.client.get(path=self.test_user_url)
        assert self.user_json_response.status_code == HTTPStatus.OK
        self.shoppinglistitem_json = {
            'item_name': 'chocolate',
            'item_quantity': '3',
            'item_brand': 'Lindt',
            'item_grocery_store': 'ALDI',
            'expected_item_price_max': '4.12',
            'buyer': self.user_json_response.data['url']
        }

    @pytest.mark.django_db
    def test_post(self):
        response = self.client.post(self.base_url, data=self.shoppinglistitem_json, format='json')

        self.assert_response_fields_equals_json_input(response, self.shoppinglistitem_json)
        self.assert_inventory_item_is_created()

    @pytest.mark.django_db
    def test_get(self):
        posted_shoppinglistitem = self.post_shoppinglistitem_and_getit_from_db()
        # get posted test data
        response = self.client.get(path=f'{self.base_url}{posted_shoppinglistitem.id}/', format='json')
        self.assert_response_fields_equals_json_input(response, self.shoppinglistitem_json)

    @pytest.mark.django_db
    def test_patch(self):
        posted_item = self.post_shoppinglistitem_and_getit_from_db()
        response = self.client.patch(path=f'{self.base_url}{posted_item.id}/',
                                     data={'item_brand': 'Continente'},
                                     format='json')
        self.assertEqual(response.status_code, HTTPStatus.OK._value_)
        self.assertEqual(response.data['item_brand'], 'Continente')

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
                                       'expected_item_price_max': self.shoppinglistitem_json['expected_item_price_max'],
                                       'buyer': self.shoppinglistitem_json['buyer']
                                   },
                                   format='json')

        self.assertEqual(response.status_code, HTTPStatus.OK._value_)
        self.assertEqual(response.data['item_brand'], 'Continente')

    @pytest.mark.django_db
    def test_when_change_to_status_SHOPPED_creates_inventory_items(self):
        posted_item = self.post_shoppinglistitem_and_getit_from_db()
        response = self.client.patch(path=f'{self.base_url}{posted_item.id}/',
                                     data={'barcode': '6813812841653','payed_price': '12.46'},
                                     format='json')
        self.assertEqual(response.status_code, HTTPStatus.OK._value_)
        response = self.client.get(path=f'{self.base_url}{posted_item.id}/', format='json')
        self.assertEqual(response.status_code, HTTPStatus.OK._value_)
        assert response.data['status'] == ShoppingListItemStatus.SHOPPED._value_
        created_datetime = response.data['created']
        saved_shoppinglistitem: ShoppingListItem = ShoppingListItem.objects.filter(created=created_datetime).get()
        self.assertIsNotNone(saved_shoppinglistitem)
        created_inv_item:InventoryItem = InventoryItem.objects.filter(shoppinglistitem=saved_shoppinglistitem).get()
        self.assertIsNotNone(created_inv_item)
        assert created_inv_item.barcode == '6813812841653'
        assert created_inv_item.payed_price == Decimal('12.46')

    @pytest.mark.django_db
    def post_shoppinglistitem_and_getit_from_db(self) -> InventoryItem:
        response = self.client.post(self.base_url, data=self.shoppinglistitem_json, format='json')
        self.assertEqual(response.status_code, HTTPStatus.CREATED._value_)
        created_datetime = response.data['created']
        self.assertIsNotNone(created_datetime)
        saved_shoppinglistitem: ShoppingListItem = ShoppingListItem.objects.filter(created=created_datetime).get()
        self.assertIsNotNone(saved_shoppinglistitem)

        return saved_shoppinglistitem

    def assert_response_fields_equals_json_input(self, response, json_input):
        assert response.data['item_name'] == json_input['name']
        assert response.data['item_grocery_store'] == json_input['grocery_store']
        assert response.data['item_brand'] == json_input['brand']
        assert response.data['buyer'] == json_input['buyer']
        assert response.data['item_quantity'] == int(json_input['quantity'])
        assert response.data['expected_item_price_max'] == int(json_input['expected_item_price_max'])
        assert response.data['status'] == ShoppingListItemStatus.CREATED._value_
        # calculated and auto fields
        self.assertIn(response.data['created'][0:9], str(now()))
        assert response.data['url'] == 'http://testserver/shoppinglistitem/1/'

    def assert_inventory_item_is_created(self):
        self.assertEqual(InventoryItem.objects.get().name, self.shoppinglistitem_json['item_name'])
        self.assertEqual(InventoryItem.objects.get().quantity, int(self.shoppinglistitem_json['item_quantity']))
        self.assertEqual(InventoryItem.objects.get().brand, self.shoppinglistitem_json['item_brand'])
        self.assertEqual(InventoryItem.objects.get().grocery_store, self.shoppinglistitem_json['item_grocery_store'])
        user = User.objects.get_by_natural_key('admin')
        self.assertEqual(InventoryItem.objects.get().creator, user)

    def assert_response_fields_equals_json_input(self, response, json_input):
        self.assertEqual(response.data['item_name'], json_input['item_name'])
        self.assertEqual(response.data['item_brand'], json_input['item_brand'])
        self.assertEqual(response.data['item_quantity'], int(json_input['item_quantity']))
        self.assertEqual(response.data['item_grocery_store'], json_input['item_grocery_store'])
        self.assertEqual(response.data['expected_item_price_max'], json_input['expected_item_price_max'])