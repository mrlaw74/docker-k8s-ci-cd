from flask import Flask, request

app = Flask(__name__)

@app.route("/github-webhook", methods=["POST"])
def webhook():
    print(request.json)
    return "OK"

app.run(port=8000)