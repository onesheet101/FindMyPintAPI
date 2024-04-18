import bcrypt

class PasswordHandler():

    def __init__(self, db):
        self.db = db

    def authenticate_user(self, username, password, queryh):

        #check and see if username exists in database need to set up interface!!!
        if self.does_user_exist(username, "userpassword") is False:
            return False

        #hashed_password will need to be retrieved from database where given username matches the username in table.
        hashed_password = queryh.get_record_item(username, "hashed_password", "username", "userpassword").encode('utf-8')

        #This hashes the given password then compares hashed password that is stored.
        if bcrypt.checkpw(password.encode('utf-8'), hashed_password):
            return True
        else:
            return False


    def does_user_exist(self, username, table):
        with self.db.cursor() as cursor:

            query = f'SELECT * FROM {table} WHERE username = %s'

            cursor.execute(query, (username,))

            record = cursor.fetchone()

            if record:
                return True
            else:
                return False


    def store_password(self, username, hashed_password, hashed_email):
        return self.queryh.add_new_sensitive_record(username, hashed_password, hashed_email)

    def update_password(self, username, hashed_password):
        with self.db.cursor() as cursor:
            query = "UPDATE userpassword SET hashed_password = %s WHERE username = %s"

            cursor.execute(query, (hashed_password, username))

            self.db.commit()
        return

    def hash_string(self, password):
        hashed_string = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        return hashed_string

    def check_user_pass_validity(self, password):

        passlength = len(password)
        if passlength <= 7 or passlength > 16:
            return False
        if not password.isascii():
            return False
        return True




        


































































































































































































































































































































































































































































































































































































































































































































