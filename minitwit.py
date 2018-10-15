# -*- coding: utf-8 -*-
"""
    MiniTwit
    ~~~~~~~~

    A microblogging application written with Flask and sqlite3.

    :copyright: © 2010 by the Pallets team.
    :license: BSD, see LICENSE for more details.
"""

import time
import requests
import json
from sqlite3 import dbapi2 as sqlite3
from hashlib import md5
from datetime import datetime
from flask import Flask, request, session, url_for, redirect, \
     render_template, abort, g, flash, _app_ctx_stack, jsonify
from werkzeug import check_password_hash, generate_password_hash


# configuration
DATABASE = '/tmp/minitwit.db'
PER_PAGE = 30
DEBUG = True
SECRET_KEY = b'_5#y2L"F4Q8z\n\xec]/'
API_BASE_URL = 'http://localhost:8080/'
# create our little application :)
app = Flask('minitwit')
app.config.from_object(__name__)
app.config.from_envvar('MINITWIT_SETTINGS', silent=True)



def format_datetime(timestamp):
    """Format a timestamp for display."""
    return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d @ %H:%M')


def gravatar_url(email, size=80):
    """Return the gravatar image for the given email address."""
    return 'https://www.gravatar.com/avatar/%s?d=identicon&s=%d' % \
        (md5(email.strip().lower().encode('utf-8')).hexdigest(), size)


@app.before_request
def before_request():
    g.user = None     
    null = None
    print "aaaaaaaaaaa"
    if session.get('user_id') is not null:
        print session['user']
        g.user = {'user_id':session['user_id'],'username':session['user']}
    



@app.route('/<username>')
def user_timeline(username):
	print "aaaaa"
	url = API_BASE_URL+username
	if g.user:
	    payload = {'user_id':session['user_id'],'username':username}
	if g.user is None:
	    payload = {'user_id':'0', 'username':username}
	r = requests.get(url,data=payload)
	
	if r is None:
	    abort(404)
	data = r.json()
	print data[0]['tweets']
	if data[1]['followed'] is True:
		return render_template('timeline.html', followed = True, profile_user = {'user_id':data[2]['author_id'],'username':data[3]['username']}, messages = data[0]['tweets'])
	else:
		return render_template('timeline.html', followed = False, profile_user = {'user_id':data[2]['author_id'],'username':data[3]['username']}, messages = data[0]['tweets'])
		


@app.route('/public')
def public_timeline():

    r = requests.get(API_BASE_URL+'public', stream=True)
   
    
    data = r.json()
    
    return render_template('timeline.html', messages = data["tweets"])
   	
   


@app.route('/')
def timeline(): 
   if g.user is None:
        return redirect(url_for('public_timeline'))
   url = API_BASE_URL+'timeline'
   payload = {'user_id':session['user_id']}
   r = requests.get(url, data=payload)
   data = r.json()
   return render_template('timeline.html', messages = data["tweets"])
   	



@app.route('/<username>/follow')
def follow_user(username):
    """Adds the current user as follower of the given user."""
    url = API_BASE_URL+'follow/'+username
    payload = {'user_id':session['user_id']}
    r = requests.get(url, data=payload)
    flash('You are now following "%s"' % username)
    return redirect(url_for('user_timeline', username=username))


@app.route('/<username>/unfollow')
def unfollow_user(username):
    """Removes the current user as follower of the given user."""
    
    url = API_BASE_URL+'unfollow/'+username
    payload = {'user_id':session['user_id']}
    r = requests.get(url, data=payload)
    
    flash('You are no longer following "%s"' % username)
    return redirect(url_for('timeline'))


@app.route('/add_message', methods=['POST'])
def add_message():
    """Registers a new message for the user."""
    if 'user_id' not in session:
        abort(401)
    if request.form['text']:
        url = API_BASE_URL+'add_message'
        payload = {'user_id':session['user_id'],'text':request.form['text']}
        r = requests.post(url,data=payload)
        data = r.json()
        flash('Your message was recorded')
    return redirect(url_for('timeline'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('timeline'))
    error = None
   
    if request.method == 'POST':
        
        url = API_BASE_URL+'login'
        payload = {'username':request.form['username'], 'password':request.form['password']}
        r = requests.post(url, data=payload)
        data = r.json()
        
        if data is None:
            error = 'Invalid username'
            
        elif not check_password_hash(data['pw_hash'],
                                     request.form['password']):
        	
        	error = 'Invalid password'
        else:
            username = data['username']
            session['user'] = username
            session['token'] = data['token']
            x = data['user_id']
            session['user_id'] = x
            print session['user_id']
                      
            flash('You were logged in')
            return redirect(url_for('public_timeline'))
	   
    return render_template('login.html', error=error)
	

    


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registers the user."""
    if g.user:
        return redirect(url_for('timeline'))
    error = None
    
    if request.method == 'POST':
        url = API_BASE_URL+'check_username'
        payload = {'username':request.form['username']}
        r = requests.post(url, data=payload)
        data = r.json()
        print data['user']
        
       
        if not request.form['username']:
            error = 'You have to enter a username'
        elif not request.form['email'] or \
                '@' not in request.form['email']:
            error = 'You have to enter a valid email address'
        elif not request.form['password']:
            error = 'You have to enter a password'
        elif request.form['password'] != request.form['password2']:
            error = 'The two passwords do not match'
        elif data['user'] == 'yes':
            error = 'The username is already taken'
        else:
		   url = API_BASE_URL+'register'
		   payload =  {
		          'username': request.form['username'],
                  'email':request.form['email'],
                  'password':generate_password_hash(request.form['password'])
			   }

		   r = requests.post(url, data=payload)
		   flash('You were successfully registered and can login now')
		   return redirect(url_for('login'))
    return render_template('register.html', error=error)


@app.route('/logout')
def logout():
    """Logs the user out."""
    flash('You were logged out')
    session.pop('user_id', None)
    return redirect(url_for('public_timeline'))


# add some filters to jinja
app.jinja_env.filters['datetimeformat'] = format_datetime
app.jinja_env.filters['gravatar'] = gravatar_url

