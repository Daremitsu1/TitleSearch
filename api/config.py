import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",       # Change if MySQL is remote
        user="root",            # Your MySQL username
        password="Yoshimitsu1!",  # Your MySQL password
        database="TitleSearch_DB",  # Our DB
        autocommit=True
    )
