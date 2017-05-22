from flask import render_template
from app import app

@app.route('/')
def hello_world():
    return 'Welcome Flask on Predix :)' 
@app.route('/index')
def index():
    user = {'nickname': 'Miguel'}  # fake user
    posts = [  # fake array of posts
        { 
            'author': {'nickname': 'John'}, 
            'body': 'Beautiful day in Portland!' 
        },
        { 
            'author': {'nickname': 'Susan'}, 
            'body': 'The Avengers movie was so cool!' 
        }
    ]
    return render_template('index/index.html',
                           title='Home',
                           posts=posts,
                           user=user)