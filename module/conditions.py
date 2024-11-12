import infermedica_api

APP_ID = "ecf0a763"
APP_KEY = "2d6b19fccbc3284c3861deb19094d8d6"

api = infermedica_api.APIv3Connector(app_id = APP_ID, app_key = APP_KEY)
print(api.info())

age = 25

print("Conditions list:")
print(api.condition_list(age=age), end="\n\n")

print("Condition details:")
print(api.condition_details("c_221", age=age), end="\n\n")

print("Non-existent condition details:")
print(api.condition_details("fail_test", age=age))