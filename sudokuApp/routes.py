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

from sudokuApp import storage 

import tensorflow as tf #used for reading images from google cloud bucket

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

def upload_image_file(file):
    if not file:
        return None
    public_url = storage.upload_file(file.read(),file.filename,file.content_type)
    return public_url

def process_picture(form_picture):
	im = Image.open(form_picture).convert('RGB') 
	#convert from PIL to openCV format, RGB to BGR 
	cvImage = np.array(im) 
	cvImage = cvImage[:, :, ::-1].copy()
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
			picture_file = upload_image_file(form.picture.data)
			session['picPath'] = picture_file
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
			session['picPath'] = 'https://00e9e64bac6c126676489ad64780f2f00d3b311366a6d4f967-apidata.googleusercontent.com/download/storage/v1/b/sudoku-image-solver/o/default.jpg?qk=AD5uMEti3nplKSOhR2Nnxb2_tWh7aXSU5hT38XKZZ9tbOPrlX-sOzr2mlCVCTyRtqK8j1dWLgR0xj69ubJcnefTPFEguYhdMYr9Oe2fzjsD7DUsF9a2OMApaNrzPnJkAhp98mIhw8fm5irQniImmDx7ta297ndvCMKkuhAKqBq1EvJYQ4o8uo7Ex528EfWMpdON4jjjafhnRnilrQwUXY-BmV5VucgEBZwsjW4TFyULVINzPu4g2NIbHb0EYbxOy89QFcZjt_HdBYEll0HRcFkXFdXbo97AA4Z6yB3ZfV7LE4UyAdpCan6HP21rEDOzvGEiphkF3Q9onlAuP44z9ABzIoZA4MuErrNvdS6qnPxMxiQUQ78Ln5V4QO2_3pa7FlGxi_DVtCogh6TKr64F76ZmfFuvcCJo-IBMgShlpi62T-LnZRObCr8LM4D0KeaBKRNGn8Lf3D0Gi4ObQFyNa_NCWBZoYU0GE2Ao0jOPRKj_SZXTGV_6rEBDLNKe8iFkfNKVmDJ9f9X_8Cn00jWPZ3FxIWj42x0zRYSmTF8F5VkljIIexu2dpk6TCNRIawGXv6ctFtPqDCu3VKWSSUH4Gv_C9dxb75byknDz6O1vxvl8S0svQZYi7mZAtw5q_sii5511egjUtmYZ6JvILn5TkXoj2YPoK-H_omO6T9N0aVWY44_M8SjC9kMoRio8RGaVAtP2eXcu28m1NBhLDd4U0zZu5xtRFb2anb3tJUwvKTINfcOvhg1wULApAJ1n-Y5FPmZoq3GaDUs0pqo6P6HfbUfSqVf8AMtKeJw'
			try:
				#no picture selected. use default
				session['procGrid'] = process_picture('sudokuApp/static/siteImages/default.jpg').tolist()

			# try 1
			# read image from google cloud bucket
			# image_path = 'gs://sudoku-image-solver/default.jpg'
			# image = tf.read_file(image_path)
			# image = tf.image.decode_jpeg(image)

			# #try 2
			# image = 'gs://sudoku-image-solver/default.jpg'
			# session['procGrid'] = process_picture(image).tolist()
			# https://stackoverflow.com/questions/44043036/how-to-read-image-file-from-s3-bucket-directly-into-memory
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
	picPath =  session['picPath']
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
	gridOut = np.array(session.get('solution', 'not set')).flatten()
	form = gridForm()
	if form.validate_on_submit():
		#gather results from form and convert None entries to 0
		gridOut = [field.data if field.data else 0 for field in form.cellVals.entries]
	return render_template('solution.html', form=form, grid=gridOut)


@app.route("/about", methods=['GET', 'POST'])
def about():
	return render_template('about.html')

