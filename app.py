from flask import Flask
from EndPoints.endpoints import setup_endpoints
from flask_jwt_extended import JWTManager
import os
import mysql.connector
from mysql.connector import Error
import ssl
from configparser import ConfigParser
from handlers.password_handler import PasswordHandler
from handlers.query_handler import QueryHandler
from handlers.post_handler import PostHandler
from handlers.generate_posts_handler import Generate
from handlers.route_handler import GoogleMapsAPI, KMeans, Route
from dotenv import load_dotenv
import googlemaps

#Uncomment line below when hosting locally.
#load_dotenv('Hidden/.env')
#Initialises the flask app library.
app = Flask(__name__)

#Gets a database connection as an object.
try:

    db = mysql.connector.connect(
        host=os.getenv("SECRET_DB_HOST"),
        user=os.getenv("SECRET_DB_USER"),
        password=os.getenv("SECRET_DB_PSWRD"),
        database=os.getenv("SECRET_DB_DATABASE"),
        port=os.getenv("SECRET_DB_PORT"),
        ssl_ca=os.getenv("SECRET_DB_SSL_CA"),
        ssl_disabled=False
    )

    if db.is_connected():
        db_info = db.get_server_info()
        print("Connected to MySQL Server version ", db_info)

except Error as e:
    print("Error while connecting to MySQL", e)

config = ConfigParser()
config.read('config.ini')

#Create secure ssl context for emails
context = ssl.create_default_context()

#This sets the private key within the flask application that will be used to encode and decode jwt's.
app.config['JWT_SECRET_KEY'] = os.getenv("SECRET_FLASK_KEY") #Will import this from seperate file so it is secure.

#This starts running the flask extension on top of it
jwt = JWTManager(app)

#This initialises an instance of the google maps api client that is passed into classes
gm = googlemaps.Client(key=os.getenv('SECRET_GET_API_KEY'))

#Create Handler Instances
passwordh = PasswordHandler(db)
queryh = QueryHandler(db)
posth = PostHandler(db, gm)
generateh = Generate(db)
gmapsh = GoogleMapsAPI(gm)
kmeansh = KMeans(gm)
routeh = Route(gm, db)

#This passes the flask and extension objects to the endpoint functions so they can use their library methods.
setup_endpoints(app, jwt, context, config, passwordh, queryh, posth, gmapsh, kmeansh, routeh, generateh)

if __name__ == '__main__':
    #Starts flask
    app.run(debug=False)

#test
