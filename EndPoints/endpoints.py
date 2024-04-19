from flask import request, jsonify
from handlers.email_handler import *
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from datetime import timedelta
import sys
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

        #If the user is authenticated create a token that lasts for 5 hours and return it to them.
        if passwordh.authenticate_user(username, password, queryh):
            user_id = queryh.get_record_item(username, "user_id", "username", "user_sensitive")
            expires = timedelta(hours=5)
            access_token = create_access_token(identity=user_id, expires_delta=expires)
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
            return jsonify({"error": "Missing a parameter"}), 400

        if not passwordh.check_user_pass_validity(password):
            return jsonify({"error": "Password format incorrect"}), 422

        if not passwordh.check_user_pass_validity(username):
            return jsonify({"error": "Username format incorrect"}), 422

        #See if username is available.
        # If user exists return error code and message.
        if passwordh.does_user_exist(username, user_table):
            return jsonify({"error": "User already exists"}), 409

        email_password = os.getenv('SECRET_EMAIL_KEY')
        if not send_confirmation(email, context, config, email_password):
            return jsonify({"error": "Email could not be sent, registration failed"}), 500

        hashed_password = passwordh.hash_string(password)
        hashed_email = passwordh.hash_string(email)

        # store hashed_password with the username in the database again need to work on implementing database functionality.
        if passwordh.store_password(username, hashed_password, hashed_email, queryh):
            user_id = queryh.get_user_id(username)
            query = "INSERT INTO user_preference (user_id, est_1, est_2, est_3, drink_1, drink_2, drink_3) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            data = (user_id, "N/A", "N/A", "N/A", "Corona", "Corona", "Corona")
            queryh.run_query(query, data, False)
            return jsonify({"message": "User registered successfully"}), 200
        else:
            return jsonify({"error": "Problem adding database record"}), 500

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
            return jsonify({'error': 'User does not own that post'}), 401

# -----------------------------------Generate Posts Handling--------------------------------------------
    @app.route('/get_feed',methods = ['GET'])
    @jwt_required()
    def get_feed():
        ##Get posts 
        query = "SELECT post_body,user_id FROM post"

        posts =queryh.get_posts(query,None,True) ##Gets 10 results 
        post_list= []

        for post in posts:
            #Get Username 
            query = "SELECT username FROM user_sensitive WHERE user = %s"
            userid = post[1]
            username  = queryh.run_query(query, (userid,),True)
            text = post[0]
            post_dict  = {'username': username, 
                            'text': text}
            post_list.append(post_dict)
        return jsonify(post_list), 200

    @app.route('/get-friend-feed',methods = ['GET'])
    @jwt_required()
    def get_friend_feed():
        try:
            user_id = get_jwt_identity()
            query = "SELECT following_user_id FROM following WHERE user_id = %s"
            friend_list = queryh.run_query(query, (user_id,), True)

            friend_feed = []

            for friend_id in friend_list:
                query = "SELECT post_body, post_time FROM post WHERE user_id = %s ORDER BY post_time DESC LIMIT 10"
                friend_posts = queryh.run_query(query, (friend_id,), True)
                
                for post in friend_posts:
                    post_body = post[0]
                    post_time = post[1]

                    # Get Username 
                    query = "SELECT username FROM user_sensitive WHERE user_id = %s"
                    username = queryh.run_query(query, (friend_id,), True)[0]

                    post_dict = {'username': username, 'text': post_body, 'time': post_time}
                    friend_feed.append(post_dict)

            # Sort the friend feed by time
            sorted_friend_feed = sorted(friend_feed, key=lambda x: x['time'], reverse=True)

            return jsonify(sorted_friend_feed[:10]), 200  # Return the first 10 posts in the sorted feed
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    @app.route('/generate-recommended-posts', methods=['GET'])
    @jwt_required()
    def generate_for_you_posts():
        user_id = get_jwt_identity()
        fy_posts = posth.getRecommendedPosts(user_id)
        loaded_posts = generateh.load_posts(fy_posts)

        return jsonify({'data': loaded_posts}), 200

    @app.route('/generate-all-posts', methods=['GET'])
    @jwt_required()
    def generate_all_posts():
        all_posts = posth.getAllPosts()
        loaded_posts = generateh.load_posts(all_posts)

        return jsonify({'data': loaded_posts}), 200

    @app.route('/generate-friends-posts', methods=['GET'])
    @jwt_required()
    def generate_friends_posts():
        user_id = get_jwt_identity()
        friends_posts = posth.getFriendsPosts(user_id)
        loaded_posts = generateh.load_posts(friends_posts)

        return jsonify({'data': loaded_posts}), 200

#----------------------------Route handling----------------------------------------------
    @app.route('/get-community-route',methods= ['GET'])
    @jwt_required()
    def get_community_routes():
        #Select all routs in saved routes db and return name and routeid
        query = "SELECT ID, Name FROM saved_routes"
        routes_list = queryh.run_query(query)
        return jsonify(routes_list), 200
    
    @app.route('/get-saved-route',methods = ['GET'])
    @jwt_required() 
    def get_route():
        routeid = request.get_json("route_id")
        query = "SELECT est_list FROM saved_routes WHERE route_id =%s"
        route_list = []
        est_list = queryh.run_query(query,routeid,True)
        for id in est_list:
            query = "SELECT est_id, name, lat, lon FROM establishment WHERE est_id = %s"
            est_info = queryh.run_query(query,id,True)
            location_dict = {
            'est_id': est_info[0],
            'est_name': est_info[1],
            'lat': est_info[2],
            'lon': est_info[3]
            }
            route_list.append(location_dict)
        
        return jsonify(location_dict), 200

    @app.route('/get-reviews', methods = ['GET'])
    @jwt_required()
    def get_establishment_reviews():
        est_id = request.get_json("est_id")
        query = "SELECT user_id, stars FROM reviews WHERE est_id = %s"
        try:
            results=  queryh.run_query(query, est_id,True)
            return jsonify(results), 200
        except:
            return jsonify({"error":"reviews could not be retrieved"}), 400

    @app.route('/save-review',methods =['POST'])
    @jwt_required()
    def save_review(self, userID, stars, public, text):
        user_id = get_jwt_identity()
        stars = request.get_json('stars')
        query = "INSERT INTO reviews (review_id,user_id, stars) VALUES (%s,%s, %s)"
        try:
            queryh.run_query(query, (user_id, stars))
            return jsonify({'message': 'Review saved successfully'}), 200
        except Exception as e:
            #print(e)
            return jsonify({'error': 'Review not saved'}), 400

    @app.route('/get-recommended-establishments', methods=['GET'])
    @jwt_required()
    def get_recommended_establishments():
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
    def get_route_locations():
        # produces x number of establishment names for the route planner
        try:
            start_point = (request.args.get('lat'), request.args.get('lon')) 
            distance = request.args.get('num')

            int_distance = int(distance)
            
            routeh.createRoute(start_point, 7, int_distance)
            full_route = routeh.getFinalRoute()

            return jsonify({'data': full_route}), 200
        except Exception as e:
            print(e, file=sys.stderr)
            return jsonify({'message': 'Unable to create route'}), 400

    @app.route('/save-route', methods=['POST'])
    @jwt_required()
    def save_route():
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

        return jsonify({'data': places}), 200

    @app.route('/get-estab-details', methods=['GET'])
    @jwt_required()
    def get_estab_details():
        try:
            coords = (request.args.get('lat'), request.args.get('lon'))
            details = gmapsh.get_establishment_details(coords)
            return jsonify({'data': details}), 200
        except Exception as e:
            return jsonify({'error': 'Unable to get details'}), 400

#------------------------------------Accounts---------------------------------------------------
    @app.route('/get-account', methods = ['GET'])
    @jwt_required()
    def get_account_details(): 
        try:
            user_id = get_jwt_identity()

            # Get username
            username_query = "SELECT username FROM user_sensitive WHERE user_id = %s"
            username = queryh.run_query(username_query, user_id, True)[0]

            # Get establishments
            est_list_query = "SELECT est_1, est_2, est_3 FROM user_preferences WHERE user_id = %s"
            establishments = queryh.run_query(est_list_query, user_id, True)

            # Get drinks
            drink_list_query = "SELECT drink_1, drink_2, drink_3 FROM user_preferences WHERE user_id = %s"
            drinks = queryh.run_query(drink_list_query, user_id, True)

            # Construct dictionary
            account_details = {
                'username': username,
                'establishments': establishments,
                'drinks': drinks
            }
        # Return as JSON
            return jsonify({"message": account_details}), 200
        except:
            return jsonify({"error":"Account details could not be retrieved"}), 400

    #Updates a ranking in user top 3 ranked pubs.
    @app.route('/update-establishment', methods=['POST'])
    @jwt_required()
    def update_establishment():
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

    # Updates a drink in top 3 ranked drinks.
    @app.route('/update-drinks', methods=['POST'])
    @jwt_required()
    def update_drink():
        data = request.get_json()
        number = data.get_json("number")
        new_name = data.get_json("drink_name")
        drink_name = "drink" + number
        user_id = get_jwt_identity()
        data = (drink_name, new_name, user_id)
        query = "UPDATE user_preferences SET %s = %s WHERE user_id =%s"
        if queryh.run_query(query, data, False):
            return jsonify({"message": "data successfully updated"}), 200
        else:
            return jsonify({"error": "Database not updated"}), 400

    #Gives the user's top three pubs.
    @app.route('/get-account-establishments', methods = ['GET'])
    @jwt_required()
    def get_account_establishments():
        user_id = get_jwt_identity()
        query = "SELECT est_1, est_2, est_3 FROM user_preferences WHERE user_id =%s"
        establishmnent_list = queryh.run_query(query, user_id, True)
        return jsonify({'data': establishmnent_list}), 200

    # Gives the user's top three drinks.
    @app.route('/get-drinks', methods = ['GET'])
    @jwt_required()
    def get_drinks():
        user_id = get_jwt_identity()
        query = "SELECT drink_1, drink_2, drink_3 FROM user_preferences WHERE user_id =%s"
        establishmnent_list = queryh.run_query(query, user_id, True)
        return jsonify({'data': establishmnent_list}), 200
    
