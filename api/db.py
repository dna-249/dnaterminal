from pymongo import MongoClient
import os

# Use a connection string from environment variables
# Set this in Vercel: Settings > Environment Variables > MONGO_URI
MONGO_URI = os.getenv("MONGO_URI")

# Lazy initialization: Connect only when needed
_client = None

def get_db():
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI)
    return _client["dnaterminal_db"]

def get_users_collection():
    db = get_db()
    return db["users"]

# Define operations using the collection getter
def create_user(username, hashed_password, role, status):
    return get_users_collection().insert_one({
        "username": username, 
        "password": hashed_password,
        "role": role,
        "status": status
    })

def get_user(username):
    return get_users_collection().find_one({"username": username})

# Note: Do not run create_index() at the module level.
# Call this once in your app lifespan if needed, or index via MongoDB Atlas.