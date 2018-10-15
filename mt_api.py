from sqlite3 import dbapi2 as sqlite3
from hashlib import md5
from datetime import datetime
from flask import Flask, request, url_for, redirect, \
     render_template, abort, g, flash, _app_ctx_stack


#from flask import Flask, request
from flask_restful import Api
from flask_jwt import JWT

from security import authenticate, identity
from user import UserRegister, login, check_username
from twit import msgList, addmsg, twitList, follow, unfollow, timeline    

DATABASE1 = '/tmp/minitwit1.db'
DATABASE2 = '/tmp/minitwit2.db'
DATABASE3 = '/tmp/minitwit3.db'
DATABASE4 = '/tmp/minitwit4.db'
PER_PAGE = 30
DEBUG = True

app = Flask('mt_api')
app.config.from_object(__name__)
app.config.from_envvar('MINITWIT_SETTINGS', silent=True)

app.secret_key = 'jose'


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    top = _app_ctx_stack.top
    if not hasattr(top, 'sqlite_db'):
        top.sqlite_db_1 = sqlite3.connect(app.config['DATABASE1'])
        top.sqlite_db_2 = sqlite3.connect(app.config['DATABASE2'])
        top.sqlite_db_3 = sqlite3.connect(app.config['DATABASE3'])
        top.sqlite_db_4 = sqlite3.connect(app.config['DATABASE4'])
        top.sqlite_db_1.row_factory = sqlite3.Row
        top.sqlite_db_2.row_factory = sqlite3.Row
        top.sqlite_db_3.row_factory = sqlite3.Row
        top.sqlite_db_4.row_factory = sqlite3.Row
        sessions = [top.sqlite_db_1, top.sqlite_db_2, top.sqlite_db_3, top.sqlite_db_4]
    return sessions

@app.teardown_appcontext
def close_database(exception):
    """Closes the database again at the end of the request."""
    top = _app_ctx_stack.top
    if hasattr(top, 'sqlite_db'):
        top.sqlite_db.close()



def init_db():
    """Initializes the database."""
    db = get_db()
    
    with app.open_resource('schema.sql', mode='r') as f:
        db[0].cursor().executescript(f.read())
        db[0].commit()
    with app.open_resource('schema.sql', mode='r') as f:
        db[1].cursor().executescript(f.read())
        db[1].commit()
    with app.open_resource('schema.sql', mode='r') as f:
        db[2].cursor().executescript(f.read())
        db[2].commit()
   
    with app.open_resource('schema_index.sql', mode='r') as f:
        db[3].cursor().executescript(f.read())
    db[3].commit()    
@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    init_db()
    print('Initialized the database.')


def populate_db():
    """Initializes the database."""
    db = get_db()
    with app.open_resource('populatedb.sql', mode='r') as f:
        db[0].cursor().executescript(f.read())
        db[0].commit()
    with app.open_resource('populatedb1.sql', mode='r') as f:
        db[1].cursor().executescript(f.read())
        db[1].commit()
    with app.open_resource('populatedb2.sql', mode='r') as f:
        db[2].cursor().executescript(f.read())
        db[2].commit()
   
@app.cli.command('populatedb')
def populatedb_command():
    """Creates the database tables."""
    populate_db()
    print('Populated the database.')

api = Api(app)



#jwt = JWT(app, authenticate, identity)

#api.add_resource(login_second, '/log')

api.add_resource(check_username, '/check_username')
api.add_resource(login, '/login')
api.add_resource(msgList, '/public')
api.add_resource(unfollow, '/unfollow/<string:username>')
api.add_resource(follow, '/follow/<string:username>')
api.add_resource(twitList, '/<string:username>')
api.add_resource(addmsg, '/add_message')
api.add_resource(UserRegister, '/register')
api.add_resource(timeline, '/timeline')
