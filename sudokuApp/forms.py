# -*- coding: utf-8 -*-
"""
Created on Fri Jun  7 08:39:56 2019

@author: jstander
"""

from flask_wtf import FlaskForm
from wtforms import IntegerField, FieldList, StringField, PasswordField, SubmitField
from wtforms.validators import NumberRange, DataRequired, Optional, ValidationError
from flask_wtf.file import FileField, FileAllowed, FileRequired

class imageUpload(FlaskForm):
    picture = FileField('Choose a sudoku image file', validators=[FileAllowed(['jpg', 'png'], 'Error: Files must be of type .png or .jpg'), Optional()])
    # optional validator: FileRequired()
    submit = SubmitField('Submit Image!')

class gridForm(FlaskForm):
    cellVals = FieldList(IntegerField(validators=[NumberRange(min=1, max=9, message=None), Optional()]), min_entries=81, max_entries=81)
    submit = SubmitField('Solve!')

