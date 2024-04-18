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
            user_id = queryh.get_record_item(username, "user_id", "username", "user_sensitive")
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
        user_table = "user_sensitive"
        data = request.get_json()

        username = data.get('username')
        password = data.get('password')
        email = data.get('email')

        # Checks if any fields are empty again.
        if not username or not password or not email:
            return jsonify({"error": "Missing a parameter"}), 403

        if not passwordh.check_user_pass_validity(password):
            return jsonify({"error": "Password format incorrect"}), 404

        if not passwordh.check_user_pass_validity(username):
            return jsonify({"error": "Username format incorrect"}), 405

        # check and see if username exists in database need to set up interface!!!
        # If user exists return error code and message.
        if passwordh.does_user_exist(username, user_table):
            return jsonify({"error": "User already exists"}), 409

        email_password = os.getenv('SECRET_EMAIL_KEY')
        if not send_confirmation(email, context, config, email_password):
            return jsonify({"error": "Email could not be sent, registration failed"}), 402

        hashed_password = passwordh.hash_string(password)
        hashed_email = passwordh.hash_string(email)

        # store hashed_password with the username in the database again need to work on implementing database functionality.
        if passwordh.store_password(username, hashed_password, hashed_email, queryh):
            user_id = queryh.get_user_id(username)
            query = "INSERT INTO user_preference (user_id, est_1, est_2, est_3, drink_1, drink_2, drink_3) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            data = (user_id, "N/A", "N/A", "N/A", "Corona", "Corona", "Corona")
            queryh.run_query(query, data, False)
            return jsonify({"message": "User registered successfully"}), 201
        else:
            return jsonify({"error": "Problem adding database record"}), 410

    #-----------------------Post Handling----------------------------------------------------------------------
    @app.route('/upload-post', methods=['POST'])
    @jwt_required()
    def upload_post():
        user_id = get_jwt_identity()
        data = request.get_json()
        body = data.get('body')
        longitude = data.get('longitude')
        latitude = data.get('latitude')
        if not latitude or not longitude:
            return jsonify({'error': 'Either latitude or longitude was not supplied.'}), 400
        if not body:
            return jsonify({'error': 'The post body was empty'}), 400
        return posth.upload_post(user_id, body, latitude, longitude)

    @app.route('/delete-post', methods=['POST'])
    @jwt_required()
    def delete_post():
        user_id = get_jwt_identity()
        data = request.get_json()
        post_id = data.get('post_id')
        if not posth.does_post_exist(post_id):
            return jsonify({'error': 'Post does not exist for given post_id'}), 404
        if posth.is_post_owner:
            posth.delete_post(post_id)
            return jsonify({'data': 'Post deleted'}), 200
        else:
            return jsonify({'error': 'User does not own that post'}), 403

# -----------------------------------Generate Posts Handling--------------------------------------------

    @app.route('/generate-recommended-posts', methods=['GET'])
    @jwt_required()
    def generateForYouPosts():

        user_id = get_jwt_identity()
        fy_posts = posth.getRecommendedPosts(user_id)
        loaded_posts = generateh.load_posts(fy_posts)

        return jsonify({'data': loaded_posts})

    @app.route('/generate-all-posts', methods=['GET'])
    @jwt_required()
    def generateAllPosts():

        all_posts = posth.getAllPosts()
        loaded_posts = generateh.load_posts(all_posts)

        return jsonify({'data': loaded_posts}), 200

    @app.route('/generate-friends-posts', methods=['GET'])
    @jwt_required()
    def generateFriendsPosts():

        user_id = get_jwt_identity()
        friends_posts = posth.getFriendsPosts(user_id)
        loaded_posts = generateh.load_posts(friends_posts)

        return jsonify({'data': loaded_posts}), 200

#----------------------------Route handling----------------------------------------------

    @app.route('/get-recommended-establishments', methods=['GET'])
    @jwt_required()
    def getRecommendedestablishments():
        # takes input coordinates and then produces establishments with the same classification around it

        try:
            start_point = request.args.get('start_point')
            #re = Recommended.GoogleMapsAPI(startPoint, searchTerm)
            attr = gmapsh.produceAttributes()
            attr = kmeansh.formDataset(attr)
            names = gmapsh.getPlaceNames()
            pred = kmeansh.buildModel(attr, 7)
            prediction = kmeansh.predictClass(start_point)

            recommended_estabs = kmeansh.sortClass(prediction, pred, names)

            return jsonify({'data': {'Recommended_establishments': str(recommended_estabs)}}), 200
        except Exception as e:
            print(e)
            return jsonify({'message': 'Unable to produce recommended establishments'}), 400


    @app.route('/create-route', methods=['GET'])
    @jwt_required()
    def getRouteLocations():
        # produces x number of establishment names for the route planner

        try:

            data = request.get_json()
            start_point = data.get('start_point')
            distance = data.get('distance')
            routeh.createRoute(start_point, 7, distance)
            full_route = routeh.getFinalRoute()
            full_route = full_route[:9]

            return jsonify({'data': full_route}), 200
            #return jsonify({'message': 'ok'}), 200
        except Exception as e:
            print(e)
            return jsonify({'message': 'Unable to create route'}), 400

    @app.route('/save-route', methods=['POST'])
    @jwt_required()
    def saveRoute():
        # Take a list of establishments, convert them to a comma seperated string then save to database

        user_id = get_jwt_identity()
        route = request.get_json()

        if routeh.saveRoute(route, user_id):
            return jsonify({'message': 'Route saved successfully'}), 200
        return jsonify({'message': 'Error: Unable to save route'}), 400

    @app.route('/get-estabs-around-point', methods=['GET'])
    @jwt_required()
    def get_estabs():
        #get list of establishments around a set of coordinates.

        coords = (request.args.get('lat'), request.args.get('lon')) 
        places = gmapsh.getEstabs(coords)

        return jsonify({'data': places})

    @app.route('/get-estab-details', methods=['POST'])
    @jwt_required()
    def get_estab_details():

        data = request.get_json()
        coords = data.get('coordinates')
        details = gmapsh.get_establishment_details(coords)

        return jsonify({'data': details})

#------------------------------------Accounts---------------------------------------------------

    @app.route('/update-establishment', methods=['POST'])
    @jwt_required()
    def update_establishment():
        #Find what estbalishments needs updating
        data = request.get_json()
        number  = data.get_json("number")
        new_name  = data.get_json("est_name")
        est_name  = "est_"+number
        user_id = get_jwt_identity()
        data = (est_name, new_name, user_id)
        query = "UPDATE user_preferences SET %s = %s WHERE user_id =%s"
        if queryh.run_query(query,data,False):
            return jsonify({"message": "data successfully updated"}), 200
        else:
            return jsonify({"error": "Database not updated"}), 400
