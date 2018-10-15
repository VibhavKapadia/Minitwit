from werkzeug.security import safe_str_cmp
from flask import jsonify, current_app
import sqlite3
from datetime import datetime, timedelta
from flask_restful import Resource, reqparse
from flask_jwt import JWT, jwt_required
import jwt
from datetime import datetime
import requests
import uuid

sqlite3.register_converter('GUID', lambda b: uuid.UUID(bytes_le=b))
sqlite3.register_adapter(uuid.UUID, lambda u: buffer(u.bytes_le))

database = ['/tmp/minitwit1.db', '/tmp/minitwit2.db', '/tmp/minitwit3.db']

class login(Resource):
   parser = reqparse.RequestParser()
   parser.add_argument('username',
        type=str,
        required=True,
        help="This field cannot be left blank!"
    )
   
   def post(self):
        data = login.parser.parse_args()

        username = data['username']
        shard_number = User.find_by_user_id(username)
        print shard_number
        #payload = {'username':username,'password':password}
        #user = User.find_by_username(username)
        connection = sqlite3.connect(database[shard_number])
        cursor = connection.cursor()

        query = "SELECT * FROM user WHERE username=?"
        result = cursor.execute(query, (username,))
        row = result.fetchone()
        if row:
            user = row
        else:
            user = None

        print user[0]

        connection.close()
        #user = {'username':user.username,'pw_hash':user.password,'email':user.email}
            
        if user:
            
	        #user_id = User.find_by_user_id(username)
	        users = {'user_id':user[1], 'username':user[2],'pw_hash':user[4],'email':user[3]}
	        print users
	        jwt_string = jwt.encode(users,'jose', algorithm='HS256')
	        data = {'user_id':user[1], 'username':users['username'],'pw_hash':users['pw_hash'],'email':users['email'], 'token':jwt_string}
	        print data
	        return data
            
        else: 
	        return None

class check_username(Resource):
   parser = reqparse.RequestParser()
   parser.add_argument('username',
        type=str,
        required=True,
        help="This field cannot be left blank!"
    )
   
   def post(self):
        data = login.parser.parse_args()
        username = data['username']
        
        connection = sqlite3.connect('/tmp/minitwit4.db')
        cursor = connection.cursor()

        query = "SELECT * FROM user WHERE username=?"
        result = cursor.execute(query, (username,))
        row = result.fetchone()
        print row
        if row:
            user = row
        else:
            user = None

        connection.close()
        
       
        #user = User.find_by_username(username)
        if user is not None:
        	return {'user':'yes'}
        else: 
            return {'user':'no'}
         
        	    	    

class User(Resource):
    TABLE_NAME = 'user'

    def __init__(self, id, username, email, password):
        self.id = id
        self.username = username
        self.email = email
        self.password = password

    @staticmethod
    def decode_token(token):
        payload = jwt.decode(token, 'jose')
        return payload['identity']
    
    @classmethod
    def find_by_user_id(cls, username):
        connection = sqlite3.connect('/tmp/minitwit4.db')
        cursor = connection.cursor()

        #query = "INSERT INTO {table} VALUES (NULL, ?)".format(table=self.TABLE_NAME)
        #cursor.execute(query, (username,))

        #connection.commit()
        
        query = "select user_id from user where username=?"
        result = cursor.execute(query, (username,)) 
        row = result.fetchone()
        print row
        shard_number = row[0] % 3      
        connection.close()
       	return shard_number

    @staticmethod
    def find_by_username(cls, username):
        connection = sqlite3.connect('/tmp/minitwit4.db')
        cursor = connection.cursor()

        query = "SELECT * FROM {table} WHERE username=?".format(table=cls.TABLE_NAME)
        result = cursor.execute(query, (username,))
        row = result.fetchone()
        if row:
            user = cls(*row)
        else:
            user = None

        connection.close()
        return user

    @classmethod
    def find_by_id(cls, username):
        connection = sqlite3.connect('/tmp/minitwit4.db')
        cursor = connection.cursor()

        query = "INSERT INTO user VALUES (NULL, ?)"
        cursor.execute(query, (username,))

        connection.commit()
        
        query = "select user_id from user where username=?"
        result = cursor.execute(query, (username,)) 
        row = result.fetchone()
        shard_number = row[0] % 3      
        connection.close()
       	return row[0]




class UserRegister(Resource):
    TABLE_NAME = 'user'

    parser = reqparse.RequestParser()
    parser.add_argument('username',
        type=str,
        required=True,
        help="This field cannot be left blank!"
    )

    parser.add_argument('email',
        type=str,
        required=True,
        help="This field cannot be left blank!"
    )
    parser.add_argument('password',
        type=str,
        required=True,
        help="This field cannot be left blank!"
    )

    def post(self):
        data = UserRegister.parser.parse_args()
		
        #if User.find_by_username(data['username']):
            #return {"message": "User with that username already exists."}, 400

        row = User.find_by_id(data['username'])
        shard_number = row % 3
        print shard_number
        
        connection = sqlite3.connect(database[shard_number])
        cursor = connection.cursor()

        query = "INSERT INTO {table} VALUES (?,?,?,?,?)".format(table=self.TABLE_NAME)
        cursor.execute(query, (uuid.uuid4(),row,data['username'],data['email'],data['password'],))

        connection.commit()
        connection.close()

	    
        return {"message": "User created successfully."}, 201
