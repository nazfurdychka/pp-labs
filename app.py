from flask import Flask
from routes import query

app = Flask(__name__)
app.register_blueprint(query)


if __name__ == '__main__':
    app.run(debug=True)
