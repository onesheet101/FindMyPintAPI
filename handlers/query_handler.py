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

    def add_new_user_sensitive_record(self, username, password, email):
        with self.db.cursor() as cursor:
            try:
                query = "INSERT INTO new_user_sensitive (username, password, email) VALUES (%s, %s, %s)"

                cursor.execute(query, (username, password, email))

                self.db.commit()
                return True
            except Exception as e:
                return False

    def run_query(self,query, data = None, fetch_results = False):#Data is a tuple, query is the string with placeholders 
        with self.db.cursor() as cursor:
            try:
                cursor.execute(query, data)
                if fetch_results:
                    results = cursor.fetchall()  # Fetch all results if needed
                    return results
                else:
                    return True  # Query executed successfully
            except Exception as e:
                print(f"Error executing query: {query}")
                print(f"Error details: {str(e)}")
                return None

    def set_up_preferences(self,user_id):
        ##Insert into userpref table null values 
        query = "INSERT INTO new_user_preference (user_id, est1, est2, est3, drink1,drink2,drink3) VALUES (%s, %s, %s, %s,%s, %s, %s)"
        return  self.run_query(query,(user_id, None, None, None,None,None,None), False)
            