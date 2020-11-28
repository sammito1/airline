from flask import Flask
app = Flask(__name__)

# index
@app.route('/')
def index():
    """ Display available flights """ 
