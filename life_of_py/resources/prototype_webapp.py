from flask import Flask, request
from markupsafe import escape

app = Flask("prototype_webapp")

@app.route("/greeter/<user_name>")
def greet_user(user_name):
    return "Hi there, " + escape(user_name)

@app.route("/api/request_info")
def request_information():
    return {
        "ip_address": request.remote_addr,
        "browser": request.headers["User-Agent"]}
