from flask import request, jsonify
from handlers.email_handler import *
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
import os


def setup_endpoints(app, jwt, context, config, passwordh, queryh, posth, gmapsh, kmeansh, routeh, generateh):

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
        if passwordh.authenticate_user(username, password, queryh):
            user_id = queryh.get_record_item(username, "user_id", "username", "userpassword")
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

        if not passwordh.check_user_pass_validity(new_password):
            return jsonify({"error": "New password format incorrect"}), 400

        if passwordh.authenticate_user(username, password):
            hashed_password = passwordh.hash_password(new_password)

            passwordh.update_password(username, hashed_password)
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

        if not passwordh.check_user_pass_validity(password):
            return jsonify({"error": "Password format incorrect"}), 400

        if not passwordh.check_user_pass_validity(username):
            return jsonify({"error": "Username format incorrect"}), 400

        # check and see if username exists in database need to set up interface!!!
        # If user exists return error code and message.
        if passwordh.does_user_exist(username, user_table):
            return jsonify({"error": "User already exists"}), 409

        email_password = os.getenv('SECRET_EMAIL_KEY')
        if not send_confirmation(email, context, config, email_password):
            return jsonify({"error": "Email could not be sent, registration failed"}), 400

        hashed_password = passwordh.hash_string(password)
        hashed_email = passwordh.hash_string(email)

        # store hashed_password with the username in the database again need to work on implementing database functionality.
        if passwordh.store_password(username, hashed_password, hashed_email):
            return jsonify({"message": "User registered successfully"}), 201
        else:
            return jsonify({"error": "Problem adding database record"}), 400

#-----------------------Post Handling----------------------------------------------------------------------
    @app.route('/upload_post', methods=['POST'])
    @jwt_required()
    def upload_post():
        user_id = get_jwt_identity()
        data = request.get_json()
        body = data.get('body')
        return posth.upload_post(user_id, body)

    @app.route('/delete_post', methods=['POST'])
    @jwt_required()
    def delete_post():
        user_id = get_jwt_identity()
        data = request.get_json()
        post_id = data.get('post_id')
        if not posth.does_post_exist(post_id):
            return jsonify({'error': 'Post does not exist for given post_id'}), 404
        if posth.is_post_owner:
            posth.deletePost(post_id)
            return jsonify({'message': 'Post deleted'}), 200
        else:
            return jsonify({'error': 'User does not own that post'}), 403

    # -----------------------------------Generate Posts Handling--------------------------------------------

    @app.route('/feed/generateForYouPosts', method=['GET'])
    @jwt_required()
    def generateForYouPosts():

        user_id = get_jwt_identity()
        fy_posts = posth.getRecommendedPosts(user_id)
        loaded_posts = generateh.load_posts(fy_posts)

        return jsonify({'username': loaded_posts[0], 'text': loaded_posts[1], 'time': loaded_posts[2]})

    @app.route('/feed/generateAllPosts', method=['GET'])
    def generateAllPosts():

        all_posts = posth.getAllPosts()
        loaded_posts = generateh.load_posts(all_posts)

        return jsonify({'username': loaded_posts[0]}, {'text': loaded_posts[1]}, {'time': loaded_posts[2]})

    @app.route('/feed/generateFriendsPosts', method=['GET'])
    def generateFriendsPosts():

        friends_posts = posth.getFriendsPosts()
        loaded_posts = generateh.load_posts(friends_posts)

        return jsonify({'username': loaded_posts[0]}, {'text': loaded_posts[1]}, {'time': loaded_posts[2]})

#----------------------------Route----------------------------------------------

    @app.route('/map/getRecommendedEstablishments', methods=['GET'])
    def getRecommendedestablishments():
        # takes input coordinates and then produces establishments with the same classification around it

        try:
            start_point = request.args.get('Start Point')
            #re = Recommended.GoogleMapsAPI(startPoint, searchTerm)
            attr = gmapsh.produceAttributes()
            attr = kmeansh.formDataset(attr)
            names = gmapsh.getPlaceNames()
            pred = kmeansh.buildModel(attr, 7)
            prediction = kmeansh.predictClass(start_point)

            recommended_estabs = kmeansh.sortClass(prediction, pred, names)

            return jsonify({'data': {'Recommended_establishments': str(recommended_estabs)}})
        except Exception as e:
            print(e)
            return jsonify({'message': 'Unable to produce recommended establishments'})


    @app.route('/map/getRouteLocations', methods=['GET'])
    def getRouteLocations():
        # produces x number of establishment names for the route planner

        try:
            start_point = request.args.get('Start Point')
            distance = request.args.get('Distance')
            routeh.createRoute(start_point, 7, distance)
            locations = routeh.getFinalRoute()
            return jsonify({'MapLocations': str(locations)})
        except Exception as e:

            return jsonify({'message': 'Unable to create route'})

    @app.route('/saveRoute', methods=['POST'])
    @jwt_required()
    def saveRoute():
        # Take a list of establishments, convert them to a comma seperated string then save to database

        user_id = get_jwt_identity()
        route = request.get_json()

        if routeh.saveRoute(route, user_id):
            return jsonify({'message': 'Route saved successfully'})
        return jsonify({'message': 'Error: Unable to save route'})




