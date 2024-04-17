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