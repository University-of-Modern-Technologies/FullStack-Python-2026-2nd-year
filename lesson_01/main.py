from flask import Flask

app = Flask(__name__)

abc = "abc"


@app.route("/")
def hello_world():
    return "<h1>Hello World!</h1>"


@app.route("/hello")
def hello():
    return "Hello from Flask!"


if __name__ == "__main__":
    app.run(debug=True)
