from flask import Flask, render_template
app = Flask(__name__)

# index
@app.route('/')
def index():
    """ Display available flights """ 
    return render_template('index.html')
