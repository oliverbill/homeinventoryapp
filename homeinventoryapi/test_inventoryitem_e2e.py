import os
from datetime import datetime
from http import HTTPStatus

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.timezone import now
from rest_framework.status import HTTP_403_FORBIDDEN
from rest_framework.test import APIClient, APITestCase

from homeinventoryapi.models import InventoryItem, ShoppingListItem, ShoppingListItemStatus, InventoryItemStatus


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
        self.base_path = reverse('inventoryitem-list')
        self.shoppinglistitem_baseurl = reverse('shoppinglistitem-list')
        self.test_user_url = f'{reverse("user-list")}{self.user.id}/'
        self.user_json_response = self.client.get(path=self.test_user_url)
        assert self.user_json_response.status_code == HTTPStatus.OK
        self.inventoryitem_json = {
            'name': 'chocolate',
            'quantity': '3',
            'barcode': '98435135138854',
            'brand': 'Lindt',
            'grocery_store': 'ALDI',
            'payed_price': '4.12',
            'min_alert': '3',
            'shoppinglistitem_id': '1',
            'status': InventoryItemStatus.STORED.value,
            'creator': self.user_json_response.data['url']
        }
        self.shoppinglistitem_json = {
            'item_name': 'chocolate',
            'item_quantity': '3',
            'item_brand': 'Lindt',
            'item_grocery_store': 'ALDI',
            'expected_item_price_max': '4.12',
            'status': ShoppingListItemStatus.CREATED.value
        }

    @pytest.mark.django_db
    def test_post_with_shoppinglistitem_not_existent(self):
        self.inventoryitem_json['shoppinglistitem_id'] = '1' # does not exists in DB
        response = self.client.post(path=self.base_path, data=self.inventoryitem_json)
        assert response.status_code == HTTPStatus.BAD_REQUEST.value
        assert response.data == 'shoppinglistitem not exists: 1'

    @pytest.mark.django_db
    def test_post_with_shoppinglistitem_not_used(self):
        self.save_an_inventory_item()
        shoppinglistitem = self.save_a_shoppinglistitem()
        self.inventoryitem_json['shoppinglistitem_id'] = '2'
        response = self.client.post(path=self.base_path, data=self.inventoryitem_json)
        assert response.status_code == HTTPStatus.CREATED.value
        self.assert_savedinventoryitem_equals_to_jsoninput(response, shoppinglistitem)

    def test_post_with_shoppinglistitem_already_used(self):
        self.save_an_inventory_item()
        self.inventoryitem_json['shoppinglistitem_id'] = '1' # already related to other inventoryitem
        response = self.client.post(path=self.base_path, data=self.inventoryitem_json)
        assert response.status_code == HTTPStatus.BAD_REQUEST.value
        assert response.data == 'shoppinglistitem already related to another inventoryitem: 1'

    def assert_savedinventoryitem_equals_to_jsoninput(self, json_response, shoppinglistitem):
        admin = User.objects.get_by_natural_key("admin")
        saved_inv:InventoryItem = InventoryItem.objects.filter(shoppinglistitem=shoppinglistitem).get()
        assert saved_inv.name == json_response.data['name']
        assert saved_inv.grocery_store == json_response.data['grocery_store']
        assert saved_inv.brand == json_response.data['brand']
        assert saved_inv.creator == admin
        assert saved_inv.quantity == json_response.data['quantity']
        assert saved_inv.status == json_response.data['status']
        shoppinglistitem_from_id = ShoppingListItem.objects.get(pk=self.inventoryitem_json['shoppinglistitem_id'])
        assert saved_inv.shoppinglistitem == shoppinglistitem_from_id
        # str_created = f'{saved_inv.created.year} {saved_inv.created.month} {saved_inv.created.month}'
        t2 = str(saved_inv.created)[0:19]
        t1 = str(datetime.strptime(json_response.data['created'][0:19],'%Y-%m-%dT%H:%M:%S'))
        assert t1 == t2
        assert saved_inv.min_alert == json_response.data['min_alert']
        assert saved_inv.stockout_at == None

    @pytest.mark.xfail(raises=HTTP_403_FORBIDDEN)
    def test_patch_raises_403(self):
        self.client.patch(path=self.base_path, data={'barcode': '98489462135135'})

    @pytest.mark.xfail(raises=HTTP_403_FORBIDDEN)
    def test_put_raises_403(self):
        self.client.patch(path=self.base_path, data={
                            'name': 'notebook',
                            'quantity': '1',
                            'brand': 'Dell',
                            'grocery_store': 'CONTINENTE',
                            'payed_price': '300.54',
                            'creator': self.user_json_response.data['url']
                        })

    @pytest.mark.django_db
    def test_get(self):
        saved_inventoryitem = self.save_an_inventory_item()
        response = self.client.get(path=f'{self.base_path}{saved_inventoryitem.id}/', format='json')
        self.assertEqual(response.status_code, HTTPStatus.OK._value_)
        self.assert_response_fields_equals_json_input(response, self.inventoryitem_json, saved_inventoryitem)

    @pytest.mark.django_db
    def test_delete(self):
        saved_inventoryitem = self.save_an_inventory_item()
        response = self.client.delete(path=f'{self.base_path}{saved_inventoryitem.id}/', format='json')
        self.assertEqual(response.status_code, HTTPStatus.NO_CONTENT._value_)
        assert len(InventoryItem.objects.filter(id=saved_inventoryitem.id)) == 0

    @pytest.mark.django_db
    def save_an_inventory_item(self):
        admin = User.objects.get_by_natural_key("admin")
        saved_shoplistitem = self.save_a_shoppinglistitem()

        newinv = InventoryItem()
        newinv.from_json(creator=admin, shoppinglistitem=saved_shoplistitem,
                         json_data=self.inventoryitem_json)
        newinv.save()
        return newinv

    @pytest.mark.django_db
    def save_a_shoppinglistitem(self):
        admin = User.objects.get_by_natural_key("admin")
        newshoppinglistitem = ShoppingListItem()
        saved_shoplistitem = newshoppinglistitem.from_json(buyer=admin, json_data=self.shoppinglistitem_json)
        saved_shoplistitem.save()
        return saved_shoplistitem

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

