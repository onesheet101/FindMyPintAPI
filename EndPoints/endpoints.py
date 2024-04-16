from flask import request, jsonify
from handlers.password_handler import *
from flask_jwt_extended import create_access_token
from datetime import timedelta
from handlers.email_handler import *
import os

def setup_endpoints(app, jwt, db, context, config):

    #-------------------------------------------------------------------------------------------------------------------
    # ----------------------------------------------PASSWORD HANDLING---------------------------------------------------
    @app.route('/login', methods=['POST'])
    def login():
        data = request.get_json()

        username = data.get('username')
        password = data.get('password')

        #Check if fields are empty.
        if not username or not password:
            return jsonify({"error": "Missing username or password"}), 400

        #If the user is authenticated create a token that lasts for thirty minutes and return it to them.
        if authenticate_user(username, password, db):
            expires = timedelta(minutes=180)
            access_token = create_access_token(identity=username, expires_delta=expires)
            return jsonify({'message': 'Login successful'}), 200, {'Authorization': access_token}
        else:
            return jsonify({'error': 'Invalid username or password'}), 401

    @app.route('/change-password', methods=['POST'])
    def change_password():

        data = request.json
        username = data.get('username')
        password = data.get('password')
        new_password = data.get('new_password')

        if not check_user_pass_validity(new_password):
            return jsonify({"error": "New password format incorrect"}), 400

        if authenticate_user(username, password, db):
            hashed_password = hash_password(new_password)

            update_password(username, hashed_password, db)
            return jsonify({'message': 'Password change successful'}), 200

        return jsonify({'error': 'Invalid username or password'}), 401

    @app.route('/register', methods=['POST'])
    def register():
        print('1', file=sys.stderr)
        user_table = "userpassword"
        data = request.get_json()

        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        print('2', file=sys.stderr)
        # Checks if any fields are empty again.
        if not username or not password or not email:
            return jsonify({"error": "Missing a parameter"}), 400
        print('3', file=sys.stderr)

        # check and see if username exists in database need to set up interface!!!
        # If user exists return error code and message.
        if does_user_exist(username, user_table, db):
            return jsonify({"error": "User already exists"}), 409
        print('4', file=sys.stderr)

        if not check_user_pass_validity(password):
            return jsonify({"error": "Password format incorrect"}), 400
        print('5', file=sys.stderr)
        if not check_user_pass_validity(username):
            return jsonify({"error": "Username format incorrect"}), 400
        print('6', file=sys.stderr)

        email_password = os.getenv('SECRET_EMAIL_KEY')
        if not send_confirmation(email, context, config, email_password):
            return jsonify({"error": "Email could not be sent, registration failed"}), 400

        print('7', file=sys.stderr)
        hashed_password = hash_password(password)

        # store hashed_password with the username in the database again need to work on implementing database functionality.
        store_password(username, hashed_password, db)

        return jsonify({"message": "User registered successfully"}), 201



