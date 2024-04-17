from flask import jsonify


class PostHandler:

    def __init__(self, db):
        self.db = db

    def upload_post(self, user_id, body):
        query = "INSERT INTO new_post (user_id, body) VALUES (%s, %s)"
        try:
            with self.db.cursor() as cursor:
                self.db.execute(query, (user_id, body))
                self.db.commit()
                return jsonify({'message': 'Post uploaded success'}), 200
        except Exception as e:
            print(e)
            return jsonify({'error': 'Post not saved'}), 500

    def is_post_owner(self, user_id, post_id):
        query = "SELECT * FROM new_post WHERE user_id = %s AND post_id = %s"

        with self.db.cursor() as cursor:
            cursor.execute(query, (user_id, post_id))
            result = cursor.fetchone()
            if result:
                return True
            else:
                return False

    def does_post_exist(self, post_id):
        query = "SELECT * FROM new_post WHERE post_id = %s"

        with self.db.cursor() as cursor:
            cursor.execute(query, (post_id))
            result = cursor.fetchone()
            if result:
                return True
            else:
                return False

    def deletePost(self, postID):
        query = "DELETE FROM new_post WHERE PostID = %s"
        try:
            self.db.execute(query, (postID))
            self.db.commit()
            return jsonify({'message': 'Post deleted successfully'})
        except Exception as e:
            print(e)
            return jsonify({'message': 'Post not deleted'}), 500