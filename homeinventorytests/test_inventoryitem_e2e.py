from datetime import datetime
from http import HTTPStatus

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.timezone import now
from rest_framework.status import HTTP_403_FORBIDDEN
from rest_framework.test import APIClient, APITestCase

from homeinventoryapi.models import InventoryItem, ShoppingListItem, InventoryItemStatus, ShoppingListStatus
from homeinventorytests.test_common import save_a_shoppinglistitem, save_an_inventory_item, inventoryitem_json

class InventoryItemE2ETest(APITestCase):

    def setUp(self):
        # os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homeinventoryapi.settings')
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='appuser',
            password='12345'
        )
        self.client.force_authenticate(user=self.user)
        self.base_path = reverse('inventoryitem-list')

    def test_post_with_shoppinglistitem_not_existent(self):
        response = self.client.post(path=self.base_path, data=inventoryitem_json)
        assert response.status_code == HTTPStatus.BAD_REQUEST.value
        assert response.data == 'shoppinglistitem does not exists: 1'

    @pytest.mark.django_db
    def test_post_with_shoppinglistitem_not_used(self):
        shoppinglistitem = save_a_shoppinglistitem(self.user)
        response = self.client.post(path=self.base_path, data=inventoryitem_json)
        assert response.status_code == HTTPStatus.CREATED.value
        self.assert_savedinventoryitem_equals_to_jsoninput(response, shoppinglistitem)

    def test_post_with_shoppinglistitem_already_used(self):
        # saved with shoplistitem_id=1
        save_an_inventory_item(self.user)
        response = self.client.post(path=self.base_path, data=inventoryitem_json)
        assert response.status_code == HTTPStatus.BAD_REQUEST.value
        assert response.data == 'shoppinglistitem already related to another inventoryitem: 1'

    def test_post_with_shorter_payload(self):
        shoppinglistitem = save_a_shoppinglistitem(self.user)
        barcode: str = inventoryitem_json['barcode']
        shorter_payload = {'barcode': barcode, 'shoppinglistitem_id': shoppinglistitem.id}
        response = self.client.post(path=self.base_path, data=shorter_payload)
        assert response.status_code == HTTPStatus.CREATED.value
        self.assert_savedinventoryitem_equals_to_jsoninput(response, shoppinglistitem)

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
                            'payed_price': '300.54'
                        })

    @pytest.mark.django_db
    def test_get(self):
        saved_inventoryitem = save_an_inventory_item(self.user)
        response = self.client.get(path=f'{self.base_path}{saved_inventoryitem.id}/', format='json')
        self.assertEqual(response.status_code, HTTPStatus.OK._value_)
        self.assert_response_fields_equals_json_input(response, inventoryitem_json, saved_inventoryitem)

    @pytest.mark.django_db
    def test_delete(self):
        saved_inventoryitem = save_an_inventory_item(self.user)
        response = self.client.delete(path=f'{self.base_path}{saved_inventoryitem.id}/', format='json')
        self.assertEqual(response.status_code, HTTPStatus.NO_CONTENT._value_)
        response = self.client.get(path=f'{self.base_path}{saved_inventoryitem.id}/', format='json')
        assert response.status_code == HTTPStatus.OK._value_
        assert response.data['status'] == InventoryItemStatus.RUNOUT._value_

    def assert_response_fields_equals_json_input(self, response, json_input, saved_inventoryitem):
        assert response.data['name'] == json_input['name']
        assert response.data['grocery_store'] == json_input['grocery_store']
        assert response.data['brand'] == json_input['brand']
        assert response.data['creator'] == f'http://testserver/users/1/'
        assert response.data['quantity'] == int(json_input['quantity'])
        # calculated and auto fields
        assert response.data['min_alert'] == int(json_input['min_alert'])
        assert response.data['shoppinglistitem'] == \
               f'http://testserver/shoppinglistitem/{saved_inventoryitem.shoppinglistitem.id}/'

        self.assertIn(response.data['created'][0:9], str(now()))
        assert response.data['stockout_at'] == None
        assert response.data['url'] == f'http://testserver/inventoryitem/{saved_inventoryitem.id}/'

    def assert_savedinventoryitem_equals_to_jsoninput(self, json_response, shoppinglistitem):
        saved_inv:InventoryItem = InventoryItem.objects.filter(shoppinglistitem=shoppinglistitem).get()
        saved_inv.refresh_from_db()
        assert saved_inv.name == json_response.data['name']
        assert saved_inv.grocery_store == json_response.data['grocery_store']
        assert saved_inv.brand == json_response.data['brand']
        assert saved_inv.creator == User.objects.get_by_natural_key('appuser')
        assert saved_inv.quantity == json_response.data['quantity']
        assert saved_inv.status == json_response.data['status']
        shoppinglistitem = ShoppingListItem.objects.get(pk=inventoryitem_json['shoppinglistitem_id'])
        assert saved_inv.shoppinglistitem == shoppinglistitem
        assert shoppinglistitem.shoppinglist.status == ShoppingListStatus.SHOPPED._value_
        # str_created = f'{saved_inv.created.year} {saved_inv.created.month} {saved_inv.created.month}'
        t2 = str(saved_inv.created)[0:19]
        t1 = str(datetime.strptime(json_response.data['created'][0:19],'%Y-%m-%dT%H:%M:%S'))
        assert t1 == t2
        assert saved_inv.min_alert == json_response.data['min_alert']
        assert saved_inv.stockout_at == None