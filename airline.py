from cs50 import SQL
from flask import Flask, render_template
app = Flask(__name__)

# index
@app.route('/')
def index():
    """ Display available flights """ 
    db = SQL("postgres://postgres:postgres@localhost:5432/COSC3380") # local db
    flights_query = db.execute("SELECT * FROM app_flights")

    # db = SQL("postgres://cosc0168:1934844MS@code.cs.uh.edu:5432/COSC3380") # remote db

    # format data in returned rows

    return render_template('index.html', rows=flights_query)
