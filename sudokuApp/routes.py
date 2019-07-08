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
from flask import Markup
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


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/puzzlePics', picture_fn)
    output_size = (500, 500)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    session['picPath'] = picture_fn
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

# def solve_puzzle(gridVerified):
# 	board = SudokuSolver(gridVerified)
# 	return board.solve()

@app.route("/", methods=['GET', 'POST'])
@app.route("/home", methods=['GET', 'POST'])
def home():
	#create form
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
				flash(Markup('Error! A Sudoku grid was not found in the image. Please try again or enter the digits manually <a href="/verify" class="alert-link">here</a>'), 'danger')
				#clear grid from previous sessions
				session['procGrid'] = np.zeros((9,9)).tolist()
				return redirect(url_for('home'))
			return redirect(url_for('verify'))
		else:	#if no picture was uploaded use default
			#put picture file path as default
			session['picPath'] = 'default.jpg'
			try:
				#no picture selected. use default
				session['procGrid'] = process_picture('sudokuApp\\static\\siteImages\\default.jpg').tolist()
			except:
				#if error occurs in image processing. reload page
				flash(Markup('Error! A Sudoku grid was not found in the image. Please try again or enter the digits manually <a href="/verify" class="alert-link">here</a>'), 'danger')
				#clear grid from previous sessions
				session['procGrid'] = np.zeros((9,9)).tolist()
				return redirect(url_for('home'))
			return redirect(url_for('verify'))
	return render_template('imageUpload.html', form=form) 


@app.route("/verify", methods=['GET', 'POST'])
def verify():
	#retrieve the grid inputs passed through the session cookie
	gridOut = np.array(session.get('procGrid', 'not set'))
	#get puzzle picture path for display
	picPath =  url_for('static', filename='puzzlePics/' + session.get('picPath', 'not set'))
	#create flask form
	form = gridForm()
	if form.validate_on_submit():
		#gather results from form and convert None entries to 0
		gridVerified = [field.data if field.data else 0 for field in form.cellVals.entries]
		gridVerified = np.array(gridVerified).reshape((9,9)) #reformat grid to be fed into solver
		#call function to solve puzzle
		board = SudokuSolver(gridVerified)
		try:
			#attempt to solve
			session['solution'] = board.solve().tolist()
			#flash(f'Sudoku Board Entries have been confirmed. Solving puzzle...', 'success')
			return redirect(url_for('solution'))
		except:   #if there is an exception give use option to correct grid or values found
			session['solution'] = board.getGrid().tolist()
			flash(Markup('Error! The program was not able to find a solution. Please recheck entries. If all entries were correct, click <a href="/solution" class="alert-link">here</a> to see partial solution.'), 'danger')
			return redirect(url_for('verify'))

	return render_template('verifyPuzzle.html', form=form, grid=gridOut.flatten(), imagePath=picPath)



@app.route("/solution", methods=['GET', 'POST'])
def solution():
	gridOut = np.array(session.pop('solution', None)).flatten()
	form = gridForm()
	if form.validate_on_submit():
		#gather results from form and convert None entries to 0
		gridOut = [field.data if field.data else 0 for field in form.cellVals.entries]
	return render_template('solution.html', form=form, grid=gridOut)


@app.route("/about", methods=['GET', 'POST'])
def about():
	return render_template('about.html')

