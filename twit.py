from flask_restful import Resource, reqparse
from flask_jwt import jwt_required
import sqlite3
from werkzeug.security import safe_str_cmp
from user import User
import jwt
from flask import request, abort, make_response, jsonify
from datetime import datetime
import time
import uuid

sqlite3.register_converter('GUID', lambda b: uuid.UUID(bytes_le=b))
sqlite3.register_adapter(uuid.UUID, lambda u: buffer(u.bytes_le))

database = ['/tmp/minitwit1.db', '/tmp/minitwit2.db', '/tmp/minitwit3.db']



class timeline(Resource):
    
    parser = reqparse.RequestParser()
    
    parser.add_argument('user_id',
        type=int,
        required=True,
        help="This field cannot be left blank!"
    )
    def get(self):
        
       	data = timeline.parser.parse_args()
        a =[]
        for x in database:			
        	connection = sqlite3.connect(x)
        	cursor = connection.cursor()
        	query = "select user.username, message.text, message.pub_date from user, message where user.user_id=message.author_id and                           (user.user_id=? or user.user_id in (select whom_id from follower where who_id = ?))"
        	result = cursor.execute(query,(data['user_id'],data['user_id'],))
        	for z in result:
					a.append({'username':z[0],'text':z[1], 'pub_date':z[2]})
        	connection.close()
				
        return {'tweets': a}

	

class msgList(Resource):

    TABLE_NAME = 'message'
    
    
    def get(self):
        items = []
        for x in database:
            query = "select message.text, message.pub_date , user.username from message, user where message.author_id = user.user_id order by message.pub_date"
            connection = sqlite3.connect(x)
            cursor = connection.cursor()
            result = cursor.execute(query)
            
            for row in result:
                items.append({'username': row[2], 'text': row[0], 'pub_date': row[1]})    
            connection.close()
        return {'tweets': items}
     

class addmsg(Resource):
    TABLE_NAME = 'message'

    parser = reqparse.RequestParser()
    parser.add_argument('text',
        type=str,
        required=True,
        help="This field cannot be left blank!"
    )
    parser.add_argument('user_id',
        type=int,
        required=True,
        help="This field cannot be left blank!"
    )	
    
	
    #@jwt_required()

    def post(self):
        data = addmsg.parser.parse_args()

        shard_number = data['user_id'] % 3
		
        connection = sqlite3.connect(database[shard_number])
        cursor = connection.cursor()

        query = "INSERT INTO {table} VALUES (?, ?, ?, ?)".format(table=self.TABLE_NAME)
        cursor.execute(query, (uuid.uuid4(),data['user_id'], data['text'], int(time.time())))

        connection.commit()
        connection.close()


        return {"message": "Tweet created successfully."}, 201


class twitList(Resource):
    TABLE_NAME = 'message'
    parser = reqparse.RequestParser()
    parser.add_argument('user_id',
        type=int,
        required=True,
        help="This field cannot be left blank!"
    )
    parser.add_argument('username',
        type=str,
        required=True,
        help="This field cannot be left blank!"
    )
	
     
    def get(self,username):
		
        data = twitList.parser.parse_args()
        
        for x in database:
        	connection = sqlite3.connect(x)
        	cursor = connection.cursor()

        	query = "SELECT user_id FROM user WHERE username=?"
        	result = cursor.execute(query, (data['username'],))
        	row = result.fetchone()
        	if row is not None:
        	    break
        
        items = twitList.find_by_id(row[0],data['username'],data['user_id'])
        return items

    @classmethod
    def find_by_id(cls,author_id,username,user_id):
        print author_id, user_id
        
        shard_number = user_id % 3
        connection = sqlite3.connect(database[shard_number])
        cursor = connection.cursor()
        query =  "select 1 from follower where who_id=? and whom_id=?"
        result  = cursor.execute(query,(user_id, author_id,))
        row  = result.fetchone()	
        if row is not None:
            followed = True
			
        else:
            followed = False
        query = "SELECT * FROM message WHERE author_id=?"
        result = cursor.execute(query, (author_id,))
        item = []
        for row in result:
            item.append({'username':username, 'text':row[2], 'pub_date':row[3]})
        connection.close()
        items = []
        print followed
        items.append({'tweets':item})
        items.append({'followed':followed})
        items.append({'author_id':author_id})
        items.append({'username':username})
        return items


class follow(Resource):
    TABLE_NAME = 'follower'

    parser = reqparse.RequestParser()
    parser.add_argument('user_id',
        type=int,
        required=True,
        help="This field cannot be left blank!"
    )
    #@jwt_required()
    def get(self, username):
        data = follow.parser.parse_args()
        shard_number = data['user_id'] % 3 
        for x in database:	
        	connection = sqlite3.connect(x)
        	cursor = connection.cursor()

        	query = "SELECT user_id FROM user WHERE username=?"
        	result = cursor.execute(query, (username,))
        	row = cursor.fetchone()
        	connection.commit()
        	if row is not None:
				break

        """if(data['user_id'] == row[0]):
            return {"message":"You cannont follow yourself"}"""

        """query = "SELECT * FROM follower WHERE who_id=? and whom_id=?"
        result = cursor.execute(query, (data['user_id'],row[0],))
        row = cursor.fetchone()

        if row is not None:
            return {"message":"You alredy follow user"}"""
            
        connection = sqlite3.connect(database[shard_number])
        cursor = connection.cursor()
        query = "INSERT INTO {table} VALUES(?, ?)".format(table=self.TABLE_NAME)
        cursor.execute(query, (data['user_id'], row[0]))
        connection.commit()
        connection.close()

class unfollow(Resource):
    TABLE_NAME = 'follower'

    parser = reqparse.RequestParser()
    parser.add_argument('user_id',
        type=int,
        required=True,
        help="This field cannot be left blank!"
    )


    #@jwt_required()
    def get(self, username):
        data = unfollow.parser.parse_args()
        shard_number = data['user_id'] % 3 
        for x in database:	
        	connection = sqlite3.connect(x)
        	cursor = connection.cursor()

        	query = "SELECT user_id FROM user WHERE username=?"
        	result = cursor.execute(query, (username,))
        	row = cursor.fetchone()
	
	        connection.commit()
	        if row is not None:
				break
          
		connection = sqlite3.connect(database[shard_number])
        cursor = connection.cursor()      
        query = "DELETE from {table} where who_id=? and whom_id=?".format(table=self.TABLE_NAME)

        cursor.execute(query, (data['user_id'], row[0],))
        connection.commit()
        connection.close()

        return {"message":"You have started Unfollwing this user"}
