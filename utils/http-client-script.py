import requests
import json

url = "https://django-cloudrun-equcscffbq-ew.a.run.app//gettoken/"

# from_sheets = {"item_name":"Coca-cola lata","item_quantity":"6","item_brand":"Coca-cola","item_grocery_store": "CONTINENTE","expected_item_price_max":"6.15","buyer": "https://django-cloudrun-equcscffbq-ew.a.run.app//users/1/"}
# from_sheets = {"username": "admin", "password": "Baleia302"}
from_sheets = {"Nome: camiseta, Marca: Hering, Quantidade: 3, Preço Limite: 5,50, Mercado de Preferência: CONTINENTE Nome: vinho, Marca: Setubal, Quantidade: 2, Preço Limite: 10, Mercado de Preferência: LIDL"}

payload = json.dumps(from_sheets)

headers = {
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
