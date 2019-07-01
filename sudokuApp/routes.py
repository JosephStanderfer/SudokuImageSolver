# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 18:37:47 2019

@author: josep
"""
import os
import time
import secrets
import cv2
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, session
from flask import Flask
from sudokuApp import app
from sudokuApp.forms import gridForm, imageUpload
import numpy as np
from sudokuApp.SudokuImageProcessor import sudokuImageProcessor
from sudokuApp.SudokuBoard import SudokuSolver


# app = Flask(__name__)
# app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
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


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/puzzlePics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn

def process_picture(form_picture):
	im = Image.open(form_picture).convert('RGB') 
	#convert from PIL to openCV format, RGB to BGR 
	cvImage = np.array(im) 
	cvImage = cvImage[:, :, ::-1].copy()
	#cvImage = cv2.imread('sudokuApp\\static\\siteImages\\default.jpg')
	#send to image processor to interpret digits
	imProcessor = sudokuImageProcessor(cvImage)
	return imProcessor.getPredictedGrid()

def solve_puzzle(gridVerified):
	board = SudokuSolver(gridVerified)
	return board.solve()

@app.route("/", methods=['GET', 'POST'])
@app.route("/home", methods=['GET', 'POST'])
def home():
	form = imageUpload()
	if form.validate_on_submit():
		if form.picture.data:
			#save sudoku puzzle picture to local directory
			picture_file = save_picture(form.picture.data)
			#use image processor class to interpret
			try:
				#process image and save to session to be used by next page
				session['procGrid'] = process_picture(form.picture.data).tolist()
			except:
				#if error occurs in image processing. reload page
				flash(f'Grid was not recognized. Please try again', 'danger')
				return redirect(url_for('home'))
			return redirect(url_for('verify'))
		else:	#if no picture was uploaded use default
			try:
				#no picture selected. use default
				session['procGrid'] = process_picture('sudokuApp\\static\\siteImages\\default.jpg').tolist()
			except:
				#if error occurs in image processing. reload page
				flash(f'Grid was not recognized. Please try again', 'danger')
				return redirect(url_for('home'))
			return redirect(url_for('verify'))
	return render_template('imageUpload.html', form=form) 


@app.route("/verify", methods=['GET', 'POST'])
def verify():
	#retrieve the grid inputs passed through the session cookie
	gridOut = np.array(session.pop('procGrid', None))

	form = gridForm()
	if form.validate_on_submit():
		#gather results from form and convert None entries to 0
		gridVerified = [field.data if field.data else 0 for field in form.cellVals.entries]
		gridVerified = np.array(gridVerified).reshape((9,9)) #reformat grid to be fed into solver
		#call function to solve puzzle
		session['solution'] = solve_puzzle(gridVerified).tolist()

		#flash(f'Sudoku Board Entries have been confirmed. Solving puzzle...', 'success')
		return redirect(url_for('solution'))
	return render_template('verifyPuzzle.html', form=form, grid=gridOut.flatten())



@app.route("/solution", methods=['GET', 'POST'])
def solution():
	#gridOut = request.args['inputGrid'] used when arguments passed over request
	#gridOut = session['confGrid']
	gridOut = np.array(session.pop('solution', None)).flatten()
	#form = populateGridForm()
	form = gridForm()
	if form.validate_on_submit():
		#gather results from form and convert None entries to 0
		gridOut = [field.data if field.data else 0 for field in form.cellVals.entries]
	return render_template('solution.html', form=form, grid=gridOut)


@app.route("/about", methods=['GET', 'POST'])
def about():
	return render_template('about.html')




# @app.route("/", methods=['GET', 'POST'])
# @app.route("/home", methods=['GET', 'POST'])
# def home():
#     form = gridForm()
#     if form.validate_on_submit():
#     	#gather results from form and convert None entries to 0
#     	gridOut = [field.data if field.data else 0 for field in form.cellVals.entries]
#     	session['confGrid'] = gridOut
#     	#if successful submission, send success message
#     	flash(f'Sudoku Board Entries have been confirmed. Solving puzzle...', 'success')
#     	return redirect(url_for('solver'))
#     return render_template('home.html', form=form, grid=grid.flatten())
 

# @app.route("/submitImage", methods=['GET', 'POST'])
# def submitImage():
# 	form = imageUpload()
# 	if form.validate_on_submit():
# 		#gather results from form and convert None entries to 0
# 		flash(f'Upload complete. Digit recognition in progress. Please wait...', 'success')
# 	return render_template('imageUpload.html', form=form)



# @app.route("/account", methods=['GET', 'POST'])
# @login_required
# def account():
#     form = UpdateAccountForm()
#     if form.validate_on_submit():
#         if form.picture.data:
#             picture_file = save_picture(form.picture.data)
#             current_user.image_file = picture_file
#         current_user.username = form.username.data
#         current_user.email = form.email.data
#         db.session.commit()
#         flash('Your account has been updated!', 'success')
#         return redirect(url_for('account'))
#     elif request.method == 'GET':
#         form.username.data = current_user.username
#         form.email.data = current_user.email
#     image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
#     return render_template('account.html', title='Account',
#                            image_file=image_file, form=form)


# if __name__ == '__main__':
#     app.run(debug=True)
