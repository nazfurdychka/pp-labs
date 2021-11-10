from app import app


@app.route('/api/v1/hello-world-26')
def hello_world():
    return 'Hello World 26!'
