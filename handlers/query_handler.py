#This function is a general purpose function to retrieve a single record of a single collumn.
def get_record_item(record_item, target_column, condition_column, table, db):
    with db.cursor() as cursor:

        query = f'SELECT {target_column} FROM {table} WHERE {condition_column} = %s'

        cursor.execute(query, (record_item,))

        record = cursor.fetchone()

        (give_item,) = record

        return give_item