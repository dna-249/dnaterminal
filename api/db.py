from pymongo import MongoClient
import os

# Use environment variables for security! 
# Never hardcode credentials in your script.
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://danamonuraa:bkJ1MVARzko9ldt9@dnaapi.hjo9y.mongodb.net/product?retryWrites=true&w=majority&appName=dnaApi")
client = MongoClient(MONGO_URI)
db = client["dnaterminal_db"]

# Collections
users_collection = db["users"]

def create_user(username, hashed_password, role, status):
    return users_collection.insert_one({
        "username": username, 
        "password": hashed_password,
        "role": role,
        "status": status
    })

def get_user(username):
    return users_collection.find_one({"username": username})
# Add this to api/db.py
def init_db():
    users_collection.create_index("username", unique=True)

# Run this once during app startup