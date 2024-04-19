from flask import jsonify
from handlers.route_handler import GoogleMapsAPI, KMeans


class PostHandler:

    def __init__(self, db, gm):
        self.db = db
        self.gm = gm

    def upload_post(self, user_id, body, lat, long):
        query = "INSERT INTO post (user_id, body, latitude, longitude) VALUES (%s, %s, %s, %s)"
        try:
            with self.db.cursor() as cursor:
                self.db.execute(query, (user_id, body, lat, long))
                self.db.commit()
                return jsonify({'message': 'Post uploaded success'}), 200
        except Exception as e:
            print(e)
            return jsonify({'error': 'Post not saved'}), 400

    def is_post_owner(self, user_id, post_id):
        query = "SELECT * FROM post WHERE user_id = %s AND post_id = %s"

        with self.db.cursor() as cursor:
            cursor.execute(query, (user_id, post_id))
            result = cursor.fetchone()
            if result:
                return True
            else:
                return False

    def does_post_exist(self, post_id):
        query = "SELECT * FROM post WHERE post_id = %s"

        with self.db.cursor() as cursor:
            cursor.execute(query, (post_id))
            result = cursor.fetchone()
            if result:
                return True
            else:
                return False

    def deletePost(self, postID):
        query = "DELETE FROM post WHERE Post_id = %s"
        try:
            with self.db.cursor():
                self.db.execute(query, (postID))
                self.db.commit()
            return jsonify({'message': 'Post deleted successfully'}), 200
        except Exception as e:
            print(e)
            return jsonify({'message': 'Post not deleted'}), 400

    classNo = 7
    searchTerm = 'pub'  # general search term for establishments
    query = 'SELECT PostID,lon,lat FROM Establishment, Post WHERE EstablishmentID == Post.Establishment AND Post.Public == True SORT BY Post.Time DESC;'  # SQL query for selecting coordinates of establishments used in public posts
    # Looks at all public posts in the database and then classifies them and gives similair reccomended to user

    def databaseQuery(self):
        try:
            with self.db.cursor():
                self.db.execute(self.query)  # execute query to get coordinates of establishments
                res = self.db.fetchall()  # store result of the query in res structure
            return res
        except:
            raise Exception('Database Connection Error: Unable to connect to database')

    def getRecommendedPosts(self, userID):
        # Uses databaseQuery and gets the coordinates of all public posts
        # Produces single attribute on all of the coordinates
        # then produces a model with them
        # then do the same with liked posts - get them all and classify on the SAME MODEL
        # Choose the most common classification then return all public posts with the same one

        # TODO
        # Format what the database returns and organise the data so that the PostID's are in postIDs list
        # and the coordinates are in the allPublic list

        allPublic = self.databaseQuery()
        allLikedPosts = self.getLikedPosts(userID)

        # Need to see how the database query will return the data
        # We want a list of coordinates and a list of PostID where the Indexes match
        postIDs = []
        pubAttr = []
        for i in allPublic:
            gm = GoogleMapsAPI(self.gm)
            pubAttr.append(gm.getSingleAttribute(allPublic[i]))

        km = KMeans(self.gm)
        data = km.formDataset(pubAttr)
        pred = km.buildModel(data, self.classNo)  # Indexes match with the PostID list

        likeClass = []
        for i in allLikedPosts:
            likeClass.append(km.predictClass(i))

        # Find most common class in likeClass then filter pred down to only those classes - use index
        # Then return postID with that index
        count = []
        for i in range(max(likeClass)):  # Fill count with 0
            count.append(0)

        for i in likeClass:
            count[i] += 1

        topClass = count.index(max(count))  # Most popular class assigned

        selected = []

        for i in range(len(pred)):
            if pred[i] == topClass:
                selected.append(postIDs[i])

        return selected  # list of postIds which are recomended

    def classify(self, coords) -> dict:
        # Provides a classification for an establishment given its coordinates and the 20 around it
        gm = GoogleMapsAPI(self.gm)  # initialise googlemaps API
        km = KMeans(self.gm)  # initialise KMeans classification

        data = gm.produceAttributes(coords)  # get attributes of establishment with given coordinates
        pID = gm.getPlaceIDs()  # get the placeIDs
        cData = km.formDataset(data)  # create the dataset for data in the correct format
        classes = km.buildModel(cData, self.classNo)

        placeClasses = {}

        for i in range(len(classes)):
            placeClasses[pID[i]] = classes[i]  # dictionary with placeID as key and value is the class of establishment

        return placeClasses  # return dictionary

    def sortByClass(self, clas: int, plaCla: dict) -> list:
        # Given an integer which represents the class return all placeIDs of the establishments with that classification value in a list
        out = []

        # Change to binary search
        for i in plaCla.keys():
            if plaCla[i] == clas:
                out.append(i)

        return out  # Return a list of all the placeID's with a classification given in the function call

    def getPostsFromPlaceIDList(self, places: list):
        res = []

        for i in places:
            with self.db.cursor():
                self.db.execute('SELECT PostID FROM Posts WHERE PlaceID=%s', i)  # execute query for selecting all posts from database from the place with placeID
                res.append(self.db.fetchall())  # add retrieved data to res structure

        return res

    def getAllPosts(self):

        query = 'SELECT PostID FROM Posts'

        with self.db.cursor():
            self.db.execute(query)
            allPosts = self.db.fetchall()

        return allPosts

    def getLikedPosts(self, userID):

        query = 'SELECT PostID FROM PostLike WHERE UserID=%s'

        try:
            with self.db.cursor():
                self.db.execute(query, userID)
                rslt = self.db.fetchall()
            return rslt
        except Exception as e:
            print(e)
            return jsonify({'message': 'Error unable to retrieve liked posts'}), 400

    def getPostLocation(self, postID):

        getEstab = 'SELECT EstablishmentID FROM Post WHERE PostID=%s'

        with self.db.cursor():
            self.db.execute(getEstab, postID)
            estabID = self.db.fetchall()

            getLatLon = 'SELECT Lat, Lon FROM Establishment WHERE ID=%s'

            self.db.execute(getLatLon, estabID)
            latLon = self.db.fetchall()

        return latLon

    def getFriendsPosts(self, userID):

        # TODO
        # Requires Testing

        with self.db.cursor():
            friendsQuery = 'SELECT Friends FROM Account WHERE UserID=%s'
            self.db.execute(friendsQuery, userID)
            friendsList = self.db.fetchall()
            friendsList = friendsList.split(',')

            query = ''
            for i in friendsList:
                query += 'SELECT PostID FROM Post WHERE UserID=' + i + ' UNION JOIN '

            query = query[:len(query) - 12]
            query += ' ORDER BY Time ASC'

            self.db.execute(query)
            friendsPosts = self.db.fetchall()

        return friendsPosts