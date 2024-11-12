import requests
import json
import infermedica_api



app_id = "ecf0a763"
app_key = "2d6b19fccbc3284c3861deb19094d8d6"

api = infermedica_api.APIv3Connector(app_id, app_key)

url = "https://api.infermedica.com/v3/parse"

text = "I feel smoach pain but no couoghing today"


age = 34

response = api.parse(text, age)

print(response)