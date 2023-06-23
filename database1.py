from mysql.connector import connect, Error
import os

try:
    with connect(
        host="localhost",
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASS'),
        database="plc_ass_scada_db"
    ) as connection:
        drop_table_query = "DROP TABLE level"
        create_water_level_table_query = """
        CREATE TABLE level(
            dt DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            level DECIMAL
        )
        """
        insert_level_query = """
        INSERT INTO level
        (level)
        VALUES
        """
        level_records = 1.0
        # values = f"({level_records[0]})"
        # for i in range(1,len(level_records)):
        #     values += f",({level_records[i]})"
            
        show_table_query = "DESCRIBE level"
        select_level_query = "SELECT * FROM level"
        # with connection.cursor() as cursor:
        #     cursor.execute(drop_table_query)
        #     connection.commit()
        # with connection.cursor() as cursor:
        #     cursor.execute(create_water_level_table_query)
        #     connection.commit()
        # with connection.cursor() as cursor:
        #     cursor.execute(insert_level_query + "(" + str(level_records) + ")")
        #     connection.commit()
            # Fetch rows from last executed query
        with connection.cursor() as cursor:
            cursor.execute(select_level_query)
            result = cursor.fetchall()
            for row in result:
                print(row)
            # connection.commit()
        # print(connection)
except Error as e:
    print(e)

