
from pymongo import MongoClient
from mongodb_config import get_connection_string, get_database_name, get_collection_name

client = MongoClient(get_connection_string())
db = client[get_database_name()]
collection = db[get_collection_name()]

result = collection.delete_many({})
print(f"Deleted {result.deleted_count} documents from '{get_collection_name()}' collection.")
