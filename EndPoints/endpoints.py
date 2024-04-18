from flask import request, jsonify
from handlers.email_handler import *
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
import os


def setup_endpoints(app, jwt, context, config, passwordh, queryh, posth):

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

        if not passwordh.check_user_pass_validity(
            
        ):
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
            try:
                query = "INSERT INTO new_user_preference (user_id, est1, est2, est3, drink1,drink2,drink3) VALUES (%s, %s, %s, %s,%s, %s, %s)"
                user_id = get_jwt_identity()
                data = (user_id, None, None, None,None,None,None)
                queryh.run_query(query, data,False)
                return jsonify({"message": "User registered successfully"}), 201
            except:
                return jsonify({'error':"Problem occured setting up user preferences"}), 400
        else:
            return jsonify({"error": "Problem adding database record"}), 400


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
            posth.deletePost(post_id)
            return jsonify({'message': 'Post deleted'}), 200
        else:
            return jsonify({'error': 'User does not own that post'}), 403




#-----------------------Account Handling----------------------------------------------------------------------
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
            return jsonify({"message": account_details})
        except:
            return jsonify("error":"Account details could not be retrieved")
    
    @app.route('/update-establishments', methods  = ['POST'])
    @jwt_required()
    def update_establishments():
        #Find what estbalishments needs updating 
        data = request.get_json()
        number  = data.get_json("number")
        new_name  = data.get_json("est_name")
        est_name  = "est_"+number
        user_id = get_jwt_identity()
        data = (est_name, new_name, user_id)
        query = "UPDATE user_preferences SET %s = %s user_id =%s" 
        if queryh.run_query(query,data,False):
            return jsonify({"message": "data successfully updated"}),200
        else:
            return jsonify({"error": "Database not updated"}),400 

    @app.route('/update-drinks', methods = ['POST'])
    @jwt_required()
    def update_drinks():#test
        ##Find what drink needs updating 
        data = request.get_json()
        number  = data.get_json("number")
        new_name  = data.get_json("drink_name")
        drink_name  = "drink"+number
        user_id = get_jwt_identity()
        data = (drink_name, new_name, user_id)
        query = "UPDATE user_preferences SET %s = %s WHERE user_id =%s" 
        if queryh.run_query(query,data,False):
            return jsonify({"message": "data successfully updated"}),200
        else:
            return jsonify({"error": "Database not updated"}),400


    @app.route('/get-establishments', methods = ['GET'])
    @jwt_required()
    def get_establishments():
        user_id = get_jwt_identity()
        query = "SELECT est_1, est_2, est_3 FROM user_preferences WHERE user_id =%s"
        estbalishmnent_list = queryh.run_query(query, user_id, True)
        return jsonify({'data': estbalishmnent_list})

    @app.route('/get-drinks', methods = ['GET'])
    @jwt_required()
    def get_drinks():
        user_id = get_jwt_identity()
        query = "SELECT drink_1, drink_2, drink_3 FROM user_preferences WHERE user_id =%s"
        estbalishmnent_list = queryh.run_query(query, user_id, True)
        return jsonify({'data': estbalishmnent_list}) 
    


#-----------------------Route Handling----------------------------------------------------------------------
    @app.route('/get-community-route',methods= ['GET'])
    @jwt_required()
    def get_community_routes():
        #Select all routs in saved routes db and return name and routeid
        query = "SELECT ID, Name FROM saved_routes"
        routes_list = queryh.run_query(query)
        return jsonify(routes_list)

    @app.route('/get-saved-route',methods = ['GET'])
    @jwt_required() 
    def get_route():
        routeid = request.get_json("route_id")
        query = "SELECT est_list FROM SavedRoutes WHERE RouteID =%s"
        route_list = []
        est_list = queryh.run_query(query,routeid,True)
        for id in est_list:
            query = "SELECT est_id, Name, Lat, Lon FROM Establishment WHERE est_id = %s"

            est_info = queryh.run_query(query,id,True)
            location_dict = {
            'est_id': est_info[0],
            'est_name': est_info[1],
            'lat': est_info[2],
            'lon': est_info[3]
            }
            route_list.append(location_dict)
        
        return jsonify(location_dict)


    @app.route('/get-reviews', methods = ['GET'])
    @jwt_required()
    def get_establishment_reviews():
        est_id = request.get_json("est_id")
        query = "SELECT user_id, stars FROM reviews WHERE est_id = %s"
        try:
            results=  queryh.run_query(query, est_id,True)
            return jsonify(results)
        except:
            return jsonify({"error":"reviews could not be retrieved"}), 400

    @app.route('/save-review',methods =['POST'])
    @jwt_required()
    def saveReview(self, userID, stars, public, text):
        user_id = get_jwt_identity()
        stars = request.get_json('stars')
        query = "INSERT INTO reviews (review_id,user_id, stars) VALUES (%s,%s, %s)"
        try:
            queryh.run_query(query, (user_id, stars))
            return jsonify({'message': 'Review saved successfully'}), 200
        except Exception as e:
            #print(e)
            return jsonify({'error': 'Review not saved'}), 400