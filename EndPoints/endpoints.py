from flask import request, jsonify
from handlers.password_handler import *
from flask_jwt_extended import create_access_token
from handlers.email_handler import *
import os
from handlers.query_handler import *

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
            user_id = get_record_item(username, "user_id", "username", "userpassword", db)
            access_token = create_access_token(identity=user_id)
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
        user_table = "userpassword"
        data = request.get_json()

        username = data.get('username')
        password = data.get('password')
        email = data.get('email')

        # Checks if any fields are empty again.
        if not username or not password or not email:
            return jsonify({"error": "Missing a parameter"}), 400


        # check and see if username exists in database need to set up interface!!!
        # If user exists return error code and message.
        if does_user_exist(username, user_table, db):
            return jsonify({"error": "User already exists"}), 409

        if not check_user_pass_validity(password):
            return jsonify({"error": "Password format incorrect"}), 400

        if not check_user_pass_validity(username):
            return jsonify({"error": "Username format incorrect"}), 400


        email_password = os.getenv('SECRET_EMAIL_KEY')
        if not send_confirmation(email, context, config, email_password):
            return jsonify({"error": "Email could not be sent, registration failed"}), 400

        hashed_password = hash_password(password)

        # store hashed_password with the username in the database again need to work on implementing database functionality.
        store_password(username, hashed_password, db)

        return jsonify({"message": "User registered successfully"}), 201



