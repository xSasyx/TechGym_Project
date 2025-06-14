from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

def get_db():
    try:
        client = MongoClient('mongodb://localhost:27017/')
        return client.universita
    except ConnectionFailure:
        print("Errore di connessione a MongoDB")
        return None