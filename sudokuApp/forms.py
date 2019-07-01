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



# class UploadForm(Form):
#     image        = FileField(u'Image File', [validators.regexp(u'^[^/\\]\.jpg$')])
#     description  = TextAreaField(u'Image Description')

#     def validate_image(form, field):
#         if field.data:
#             field.data = re.sub(r'[^a-z0-9_.-]', '_', field.data)

# def upload(request):
#     form = UploadForm(request.POST)
#     if form.image.data:
#         image_data = request.FILES[form.image.name].read()
#         open(os.path.join(UPLOAD_PATH, form.image.data), 'w').write(image_data)




#     def validate_username(self, username):
#         user = User.query.filter_by(username=username.data).first()
#         if user:
#             raise ValidationError('That username is taken. Please choose another one')
#     def validate_email(self, email):
#         user = User.query.filter_by(email=email.data).first()
#         if user:
#             raise ValidationError('That email is taken. Please choose another one')

# class LoginForm(FlaskForm):
#     email = StringField('Email',
#                         validators=[DataRequired(), Email()])
#     password = PasswordField('Password', validators=[DataRequired()])
#     remember = BooleanField('Remember Me')
#     submit = SubmitField('Login')