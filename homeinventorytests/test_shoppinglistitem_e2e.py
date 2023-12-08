from http import HTTPStatus

import pytest
from _decimal import Decimal
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.timezone import now
from rest_framework.status import HTTP_403_FORBIDDEN
from rest_framework.test import APIClient, APITestCase

from homeinventoryapi.models import ShoppingListStatus, ShoppingList, ShoppingListItem
from homeinventorytests.test_common import save_a_shoppinglistitem, shoppinglistitem_json

class ShoppingListItemE2ETest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="appuser",
            password='12345'
        )
        self.client.force_authenticate(user=self.user)
        self.base_url = reverse('shoppinglistitem-list')

    @pytest.mark.django_db
    def test_post_shoppinglistitem(self):
        shoplist = ShoppingList.objects.create(buyer=self.user)
        assert shoplist is not None
        shoppinglistitem = save_a_shoppinglistitem(self.user)
        self.assert_saved_equals_json_input(shoppinglistitem=shoppinglistitem,
                                            json_input=shoppinglistitem_json)

    @pytest.mark.django_db
    def test_post_shoppinglist(self):
        shoplist = ShoppingList.objects.create(buyer=self.user)
        assert shoplist is not None
        self.assertIsNotNone(shoplist)
        assert shoplist.status == ShoppingListStatus.CREATED
        now_edited = now().replace(microsecond=0).replace(second=0)
        created_edited = shoplist.created.replace(microsecond=0).replace(second=0)
        assert created_edited == now_edited

    @pytest.mark.django_db
    def test_get_shoppinglistitem(self):
        shoppinglistitem = save_a_shoppinglistitem(self.user)
        response = self.client.get(path=f'{self.base_url}{shoppinglistitem.id}/', format='json')
        self.assert_get_equals_json_input(response=response, json_input=shoppinglistitem_json,
                                          shoppinglistitem_id=shoppinglistitem.id)

    @pytest.mark.django_db
    def test_get_shoppinglist(self):
        shoplist = ShoppingList.objects.create(buyer=self.user)
        assert shoplist is not None
        response = self.client.get(path=reverse("shoppinglist-detail", args='1'))
        assert response.status_code == HTTPStatus.OK._value_
        assert response.data['status'] == ShoppingListStatus.CREATED._value_
        assert response.data['created'][0:9] in str(now())
        assert response.data['buyer'] == 'http://testserver/users/1/'

    @pytest.mark.xfail(raises=HTTP_403_FORBIDDEN)
    def test_patch_shoplist(self):
        self.client.patch(path=reverse("shoppinglist-detail", args="1"),
                          data={'status': ShoppingListStatus.CREATED._value_}, format='json')

    @pytest.mark.xfail(raises=HTTP_403_FORBIDDEN)
    def test_put_shoplist(self):
        self.client.put(path=reverse("shoppinglist-detail", args="1"),
                          data={'status': ShoppingListStatus.CREATED._value_}, format='json')

    @pytest.mark.django_db
    def test_patch_shoplist_item(self):
        shoppinglistitem = save_a_shoppinglistitem(self.user)
        response = self.client.patch(path=f'{self.base_url}{shoppinglistitem.id}/',
                                     data={'item_brand': 'Continente',
                                           'expected_item_price_max': '5.64'},
                                     format='json')
        self.assertEqual(HTTPStatus.OK._value_, response.status_code)

        shoppinglistitem.refresh_from_db()
        self.assertEqual('Continente', shoppinglistitem.item_brand)
        self.assertEqual(Decimal('5.64'), shoppinglistitem.expected_item_price_max)


    @pytest.mark.django_db
    def test_put_shopilistitem(self):
        shoppinglistitem = save_a_shoppinglistitem(self.user)
        assert shoppinglistitem is not None
        shoppinglistitem_json['shoppinglist'] = f'http://testserver/shoppinglist/{shoppinglistitem.shoppinglist.id}/'
        json = shoppinglistitem_json
        json['item_brand'] = 'Continente'
        response = self.client.put(path=f'{self.base_url}{shoppinglistitem.id}/',
                       ## PUT tem q passar todos os fields, senao da HTTP 400:
                                # campo c preenchimento obrigatorio
                       data=json,
                       format='json')
        assert response.status_code == HTTPStatus.OK._value_
        shoppinglistitem.refresh_from_db()
        self.assertEqual('Continente', shoppinglistitem.item_brand)

    def assert_saved_equals_json_input(self, shoppinglistitem, json_input):
        assert shoppinglistitem.item_name == json_input['item_name']
        assert shoppinglistitem.item_grocery_store == json_input['item_grocery_store']
        assert shoppinglistitem.item_brand == json_input['item_brand']
        assert shoppinglistitem.item_quantity == json_input['item_quantity']
        assert shoppinglistitem.expected_item_price_max == Decimal(json_input['expected_item_price_max'])
        # calculated and auto fields
        assert str(shoppinglistitem.created)[0:9] in str(now())

    def assert_get_equals_json_input(self, json_input, response, shoppinglistitem_id):
        assert response.data['item_name'] == json_input['item_name']
        assert response.data['item_grocery_store'] == json_input['item_grocery_store']
        assert response.data['item_brand'] == json_input['item_brand']
        assert response.data['item_quantity'] == int(json_input['item_quantity'])
        assert response.data['expected_item_price_max'] == json_input['expected_item_price_max']
        # calculated and auto fields
        self.assertIn(response.data['created'][0:9], str(now()))
        assert response.data['url'] == f'http://testserver/shoppinglistitem/{shoppinglistitem_id}/'

