import requests
import json

url = "https://django-cloudrun-equcscffbq-ew.a.run.app//shoppinglistitem/"

from_sheets = {"item_name":"Coca-cola lata","item_quantity":"6","item_brand":"Coca-cola","item_grocery_store": "CONTINENTE","expected_item_price_max":"6.15","buyer": "https://django-cloudrun-equcscffbq-ew.a.run.app//users/1/"}

payload = json.dumps(from_sheets)

headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Token  21cd58f7cbfc2af0d59f234714cbe59967d489a1',
  'X-API-Key': '{{token}}'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
