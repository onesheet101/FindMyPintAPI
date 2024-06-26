import bcrypt


class PasswordHandler():

    def __init__(self, db):
        self.db = db

    def authenticate_user(self, username, password, queryh):

        #Check and see if username exists in database.
        if self.does_user_exist(username, "user_sensitive") is False:
            return False

        #Retrieve hashed_password from database.
        hashed_password = queryh.get_record_item(username, "hashed_password", "username", "user_sensitive").encode('utf-8')

        #Compares hashed password, with given password and returns true if they are the same.
        if bcrypt.checkpw(password.encode('utf-8'), hashed_password):
            return True
        else:
            return False

    #Checks if username exists in database.
    def does_user_exist(self, username, table):
        with self.db.cursor() as cursor:

            query = f'SELECT * FROM {table} WHERE username = %s'

            cursor.execute(query, (username,))

            record = cursor.fetchone()

            if record:
                return True
            else:
                return False

    #Stores hashed_password in database with username and hashed_email.
    def store_password(self, username, hashed_password, hashed_email, queryh):
        return queryh.add_user_sensitive_record(username, hashed_password, hashed_email)

    #Updates hashed password for a username in database.
    def update_password(self, username, hashed_password):
        with self.db.cursor() as cursor:
            query = "UPDATE user_sensitive SET hashed_password = %s WHERE username = %s"

            cursor.execute(query, (hashed_password, username))

            self.db.commit()
        return

    #Hashes given string using bcrypt
    def hash_string(self, to_hash):
        hashed_string = bcrypt.hashpw(to_hash.encode('utf-8'), bcrypt.gensalt())
        return hashed_string

    #Simple error checks on valid passwords to store.
    def check_user_pass_validity(self, password):
        passlength = len(password)
        if passlength <= 7 or passlength > 16:
            return False
        if not password.isascii():
            return False
        return True




        


































































































































































































































































































































































































































































































































































































































































































































