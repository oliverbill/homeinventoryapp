from datetime import datetime, timedelta
from http import HTTPStatus

from django.urls import reverse
from django.utils.timezone import now
from rest_framework.authtoken.admin import User
from rest_framework.test import APIClient, APITestCase

from homeinventoryapi.models import InventoryItem
from homeinventorytasks.calculate_stockout_date import main as calc
from homeinventorytests.test_common import save_an_inventory_item, create_similar_inventoryitems

USERNAME = 'alves.bill'
class CalculateStockoutDateTest(APITestCase):

    def setUp(self):
        # os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homeinventoryapi.settings')
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="appuser",
            password='12345'
        )
        self.client.force_authenticate(user=self.user)

    def test_set_stockout_to_10_days_from_now(self):
        inv: InventoryItem = save_an_inventory_item(self.user, barcode='987986976796')
        similar_items, secs = create_similar_inventoryitems(self.user)
        calc(inv.id, similar_items)# avg aprox 10 days
        inv.refresh_from_db()
        assert inv.stockout_at is not None
        date_from_input = inv.created + timedelta(seconds=secs)
        assert inv.stockout_at == date_from_input

