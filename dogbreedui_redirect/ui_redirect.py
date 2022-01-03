from flask import Flask, redirect
import os

# Simple UI redirect from http to https

app = Flask(__name__)

@app.route('/')
def httptohttps():
    return redirect(str(os.environ.get("DOGBREEDUI_URL")))
if __name__ == "__main__":
    app.run(host='0.0.0.0', port='80', debug=False)
