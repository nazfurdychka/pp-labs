## Repository for programming labs

### Student id: 26 ('python 3.8.*', 'virtualenv + requirements.txt')

#### Clone repository from GitHub : https://github.com/nazfurdychka/pp-labs.git

#### Create virtual environment: 
 - go to your project directory
 - create your virtual environment using ``virtualenv .venv``

#### Activate virual environment:
``source venv/Scripts/activate``

#### Install all requirements
``pip install -r requirements.txt``

#### Run WSGI server
``waitress-serve --listen=*:5000 hello:app``

#### Check work
http://127.0.0.1:5000/api/v1/hello-world-26 
 
