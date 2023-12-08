import json
import os
import sys
from datetime import timedelta, datetime

import django
from django.conf import settings

django.setup()
from django.contrib.postgres.search import SearchVector

from homeinventoryapi.models import InventoryItem, ShoppingListItem

# Retrieve Job-defined env vars
TASK_INDEX = os.getenv("CLOUD_RUN_TASK_INDEX", 0)
TASK_ATTEMPT = os.getenv("CLOUD_RUN_TASK_ATTEMPT", 0)
# Retrieve User-defined env vars
INVENTORY_ID = os.getenv("INVENTORY_ID", None)
# DB_CONFIG = settings.DATABASES

def main(INVENTORY_ID, similar_items=None):
    print(f"Starting Task #{TASK_INDEX}, Attempt #{TASK_ATTEMPT}...")
    inventory_item = InventoryItem.objects.get(pk=INVENTORY_ID)

    if not similar_items:
        similar_items = do_postgres_fulltextsearch(inventory_item)
    calculate_stockout_at(inventory_item, similar_items)
    print(f"inv item {inventory_item.id} stockout_at: {inventory_item.stockout_at}")


def do_postgres_fulltextsearch(inv_item: InventoryItem):
    s_term = inv_item.name + " " + inv_item.brand
    query = InventoryItem.objects.annotate(search=SearchVector("name", "brand")) \
        .filter(search=s_term)
    if query:
        return query.get()
    else:
        raise ValueError("no similar inventory item found in DB")

def calculate_stockout_at(inventory_item, similar_items):
    invalid_items = [item for item in similar_items if type(item) != InventoryItem or not item.runout_at or not item.created]
    if len(invalid_items) > 0: raise ValueError('invalid similar_items. They should be of type InventoryItem and '
                                                'have runout_at and created filled in')
    all_consumption_seconds = []
    for item in similar_items:
        assert item.runout_at.date() > item.created.date(), f'runout_at date {item.runout_at} shoud be after ' \
                                                            f'created date {item.created}'
        similaritem_consumption_totalseconds = (item.runout_at.date() - item.created.date()).total_seconds()
        all_consumption_seconds.append(similaritem_consumption_totalseconds)
    avg_consumption_seconds = round(sum(all_consumption_seconds) / len(all_consumption_seconds))
    inventory_item.stockout_at = inventory_item.created + timedelta(seconds=avg_consumption_seconds)
    inventory_item.save()


if __name__ == "__main__":
    try:
        main(INVENTORY_ID)
    except Exception as err:
        message = (f"Task #{TASK_INDEX}, " + f"Attempt #{TASK_ATTEMPT} failed: {str(err)}")
        print(json.dumps({"message": message, "severity": "ERROR"}))
        sys.exit(1)  # Retry Job Task by exiting the process

