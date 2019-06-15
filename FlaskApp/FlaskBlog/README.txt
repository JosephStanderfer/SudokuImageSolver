Follows build process outlined in: https://www.youtube.com/watch?v=MwZwr5Tvyxo&list=PL-osiE80TeTs4UjLw5MM6OjgkjFeUxCYH





#to create the database
cd "folder path"
from flask_blog import db
db.create_all()

#to create users and posts
from flask_blog import User, Post
user_1 = User(username='asdf', email='cnn@safd.com', password='password')
db.session.add(user_1) #add to db
db.session.commit()

#to query the database
User.query.get(1)
User.query.all()


#to delete the database
db.drop_all()

