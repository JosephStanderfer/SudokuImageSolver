# -*- coding: utf-8 -*-
"""
Created on Tue Mar 12 16:21:52 2019

@author: josep
"""

import numpy as np
import SudokuBoard as sb
import SudokuImageProcessor as sip
import cv2
from tkinter.filedialog import askopenfilename
from tkinter import *

fname = ''
def openFile():
    global fname
    fname = askopenfilename()
    root.destroy()
    return fname

print()
print('Select your sudoku image file: ')
root = Tk()
fname = openFile()
#Button(root, text='File Open', command = openFile).pack(fill=X)
#mainloop()
image = cv2.imread(fname)
#works: sudokusmall, airplanSudoku
#fails: AAeasy, AAmedium, sudoku1, 

imProcessor = sip.sudokuImageProcessor(image)
imProcessor.printGrid()
gridEntries = imProcessor.getPredictedGrid()
#
# print grid as image
#
#
#ask user if the grid is correct. If not, have them enter the row(1-9) and column(1,9)
# of the incorrect digit (enter 0 to delete). Also print out a grid for them with rows
# and columns labeled as they select

board = sb.SudokuSolver(gridEntries)
solution = board.solve()
#
#
#if solution cannot be found, print message and ask if they would like remaining
#candidates to be displayed
#
#if solution is found, print out image in picture format with print letters as
#preset and handwritten ones as fill in's. Save grid image and standard print/hand
#letters to use

print()
print('Solution: ')
board.printGrid()

