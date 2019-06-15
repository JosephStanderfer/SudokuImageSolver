# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 18:37:47 2019

@author: josep
"""

from flask import render_template, url_for, flash, redirect
from flask import Flask
from forms import gridForm

app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

#from flask_sqlalchemy import SQLAlchemy
#from flask_bcrypt import Bcrypt
#db = SQLAlchemy(app)
#bcrypt = Bcrypt(app)

firstRow = [1,2,3,4,5,6,7,8,9]

@app.route("/")
@app.route("/home")
def home():
    form = gridForm()
    if form.validate_on_submit():
        flash('Message', 'danger')
    return render_template('home.html', entries=firstRow, form=form)


#@app.route("/register", methods=['GET', 'POST'])
#def register():
#    word = 'bean'
#    form = RegistrationForm()
#    if form.validate_on_submit():
#        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
#        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
#        db.session.add(user)
#        db.session.commit()
#        flash(f'Your account has been created. You are now ready to login.', 'success')
#        return redirect(url_for('home'))
#    return render_template('register.html', title='Register', form=form)
#
#
#@app.route("/login", methods=['GET', 'POST'])
#def login():
#    form = LoginForm()
#    if form.validate_on_submit():
#        if form.email.data == 'admin@blog.com' and form.password.data == 'password':
#            flash('You have been logged in!', 'success')
#            return redirect(url_for('home'))
#        else:
#            flash('Login Unsuccessful. Please check username and password', 'danger')
#    return render_template('login.html', title='Login', form=form)


if __name__ == '__main__':
    app.run(debug=True)
