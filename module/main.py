import infermedica_api

APP_ID = "ecf0a763"
APP_KEY = "2d6b19fccbc3284c3861deb19094d8d6"

api = infermedica_api.APIv3Connector(app_id = APP_ID, app_key = APP_KEY)
print(api.info())

# Prepare initial patients diagnostic information.
sex = "female"
age = 32
evidence = [
    {"id": "s_21", "choice_id": "present", "source": "initial"},
    {"id": "s_98", "choice_id": "present", "source": "initial"},
    {"id": "s_107", "choice_id": "present"}
]

# call diagnosis
response = api.diagnosis(evidence=evidence, sex=sex, age=age)

# Access question asked by API
print(response["question"])
print("\n")
print(response["question"]["text"])  # actual text of the question
print("\n")
print(response["question"]["items"])  # list of related evidence with possible answers
print("\n")
print(response["question"]["items"][0]["id"])
print("\n")
print(response["question"]["items"][0]["name"])
print("\n")
print(response["question"]["items"][0]["choices"])  # list of possible answers
print("\n")
print(response["question"]["items"][0]["choices"][0]["id"])  # answer id
print("\n")
print(response["question"]["items"][0]["choices"][0]["label"])  # answer label
print("\n")

# Check the "should_stop" flag
print(response["should_stop"])
print("\n")

# Next update the request and get next question:
evidence.append({
    "id": response["question"]["items"][0]["id"],
    "choice_id": response["question"]["items"][0]["choices"][0]["id"]  # Just example, the choice_id shall be taken from the real user answer
})

# call diagnosis method again
response = api.diagnosis(evidence=evidence, sex=sex, age=age)

# ... and so on, continue the interview and watch for the "should_stop" flag. 
# Once the API returns a "should_stop" flag with the value set to true, the interview questions should stop and you can present the condition results:

# Access list of conditions with probabilities
print(response["conditions"])
print("\n")
print(response["conditions"][0]["id"])
print("\n")
print(response["conditions"][0]["name"])
print("\n")
print(response["conditions"][0]["probability"])
print("\n")