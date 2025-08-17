import mysql.connector
from pymongo import MongoClient

def get_db_connection():
    """Returns MySQL database connection."""
    return mysql.connector.connect(
        host="localhost",           # Change if MySQL is remote
        user="root",                # Your MySQL username
        password="Yoshimitsu1!",    # Your MySQL password
        database="TitleSearch_DB",  # Our MySQL database
        autocommit=True
    )

def get_mongo_connection():
    """Returns MongoDB collection handle."""
    client = MongoClient("mongodb://localhost:27017/")  # Adjust if remote MongoDB
    db = client["titlesearchdoc_db"]                    # Database name
    collection = db["key_data"]                         # Collection name
    return collection
