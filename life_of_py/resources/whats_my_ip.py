import requests

response = requests.get("https://ifconfig.co/json").json()
print("My external address is " + response["ip"])

if response["country_eu"]:
    print("Looks like I'm in the European Union!")
