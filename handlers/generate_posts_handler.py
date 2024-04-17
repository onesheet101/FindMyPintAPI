import mysql.connector
from flask import Flask, request, jsonify


# ====== PersonalPosts name change!!!

class Generate:
    # static generation of posts
    # - Take list of postID's and format and order so that x amount are on a page and more can be generated
    # Need a message if no more posts can be shown

    bufferSize = 100

    def __init__(self, db):
        self.db = db

    def formatPost(self, postID):

        username = self.getUsername(self.getUserID(postID))
        time = self.getTime(postID)
        text = self.getText(postID)
        estabID = self.getEstablishmentID(postID)

        out = []
        out.append(username)
        out.append(text)
        out.append(time)
        return out

    def getData(self, posts: list):
        # get post data for the list of postID's

        try:
            query = 'SELECT UserID, Time, Text, Photo, LikeList, EstablishmentID FROM Post WHERE PostID=%s'

            self.allPosts = []

            for i in posts:
                with self.db.cursor():
                    self.db.execute(query, i)
                    self.allPosts.append(self.db.fetchall())

            return self.allPosts

        except Exception as e:
            print(e)
            return False

    # fetchall returns a list of tuples -> where each tuple is a row from the database

    def getPostAttribute(self, postID, index):
        for i in self.allPosts:
            if i[0] == postID:
                return i[index]
            else:
                return False

    def getUserID(self, postID):
        return str(self.getPostAttribute(postID, 0))

    def getTime(self, postID):
        return str(self.getPostAttribute(postID, 1))

    def getText(self, postID):
        return str(self.getPostAttribute(postID, 2))

    def getPhoto(self, postID):
        return str(self.getPostAttribute(postID, 3))

    def getLikeList(self, postID):
        return str(self.getPostAttribute(postID, 4))

    def getEstablishmentID(self, postID):
        return str(self.getPostAttribute(postID, 5))

    def setBufferSize(self, val):
        self.bufferSize = val

    def getBufferSize(self):
        return self.bufferSize

    def load_posts(self, posts):

        all_posts = self.getData(posts)
        selectedPosts = []

        amount = max(self.bufferSize, len(posts))

        for i in range(amount):
            selectedPosts.append(self.formatPost(posts[i]))

        return selectedPosts

    def getUsername(self, userIDList):
        # given a list of user IDs find the account username that it corresponds to - accept lists of 1 also
        try:
            query = 'SELECT Username FROM Account WHERE UserID=%s'

            usernames = []
            for i in userIDList:
                with self.db.cursor():
                    self.db.execute(query, i)
                    usernames.append(self.db.fetchall())
        except Exception as e:
            return False

        return usernames