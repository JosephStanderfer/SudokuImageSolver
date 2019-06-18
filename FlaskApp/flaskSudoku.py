# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 18:37:47 2019

@author: josep
"""

from flask import render_template, url_for, flash, redirect, request, session
from flask import Flask
from forms import gridForm, imageUpload
import numpy as np

app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

#from flask_sqlalchemy import SQLAlchemy
#from flask_bcrypt import Bcrypt
#db = SQLAlchemy(app)
#bcrypt = Bcrypt(app)

grid = np.zeros((9,9), dtype=np.int)
        
grid[0,0] = 8

grid[1,2] = 3
grid[1,3] = 6

grid[2,1] = 7
grid[2,4] = 9
grid[2,6] = 2

grid[3,1] = 5
grid[3,5] = 7

grid[4,4] = 4
grid[4,5] = 5
grid[4,6] = 7

grid[5,3] = 1
grid[5,7] = 3

grid[6,2] = 1
grid[6,7] = 6
grid[6,8] = 8

grid[7,2] = 8
grid[7,3] = 5
grid[7,7] = 1

grid[8,1] = 9
grid[8,6] = 4


@app.route("/", methods=['GET', 'POST'])
@app.route("/home", methods=['GET', 'POST'])
def home():
    form = populateGridForm()
    if form.validate_on_submit():
    	#gather results from form and convert None entries to 0
    	gridOut = [field.data if field.data else 0 for field in form.cellVals.entries]
    	session['confGrid'] = gridOut
    	#if successful submission, send success message
    	flash(f'Sudoku Board Entries have been confirmed. Solving puzzle...', 'success')
    	return redirect(url_for('solver'))
    return render_template('home.html', form=form, grid=grid.flatten())
 

# @app.route("/solver", methods=['GET', 'POST'])
# def solver():
# 	return render_template('solver.html')

@app.route("/solver", methods=['GET', 'POST'])
def solver():
	#gridOut = request.args['inputGrid'] used when arguments passed over request
	gridOut = session['confGrid']
	form = populateGridForm()
	if form.validate_on_submit():
		#gather results from form and convert None entries to 0
		gridOut = [field.data if field.data else 0 for field in form.cellVals.entries]
		flash(f'Sudoku Board Entries have been confirmed. Solving puzzle...', 'success')
	return render_template('home.html', form=form, grid=gridOut)


@app.route("/submitImage", methods=['GET', 'POST'])
def submitImage():
	form = imageUpload()
	if form.validate_on_submit():
		#gather results from form and convert None entries to 0
		flash(f'Upload complete. Digit recognition in progress. Please wait...', 'success')
	return render_template('solver.html', form=form)
    


if __name__ == '__main__':
    app.run(debug=True)
