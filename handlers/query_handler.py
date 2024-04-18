class QueryHandler:

    def __init__(self, db):
        self.db = db

#This function is a general purpose function to retrieve a single record of a single collumn.
    def get_record_item(self, record_item, target_column, condition_column, table):
        with self.db.cursor() as cursor:

            query = f'SELECT {target_column} FROM {table} WHERE {condition_column} = %s'

            cursor.execute(query, (record_item,))

            record = cursor.fetchone()

            (give_item,) = record

            return give_item

    def add_user_sensitive_record(self, username, password, email):
        with self.db.cursor() as cursor:
            try:
                query = "INSERT INTO user_sensitive (username, password, email) VALUES (%s, %s, %s)"

                cursor.execute(query, (username, password, email))

                self.db.commit()
                return True
            except Exception as e:
                return False

