from flask import Flask

app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['PROJECT_ID'] = 'sudoku-image-solver'
app.config['CLOUD_STORAGE_BUCKET'] = 'sudoku-image-solver'

from sudokuApp import routes