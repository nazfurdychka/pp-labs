from flask import Flask
from routes import query
from flask_cors import CORS

app = Flask(__name__)
app.register_blueprint(query)
CORS(app)

if __name__ == '__main__':
    app.run(debug=True)
