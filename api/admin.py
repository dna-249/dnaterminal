from fastapi import APIRouter, Depends, HTTPException
from api.db import db # Your MongoDB instance
from bson import ObjectId
from api.auth import get_current_user 


router = APIRouter()

# Security: Only admins can call these
def verify_admin(user = Depends(get_current_user)):
    print(f"DEBUG: Current user payload: {user}")  # Add this
    # if user.get("role") != "admin":
    #     raise HTTPException(status_code=403, detail="Admin access required")
    return user

@router.get("/users")
async def get_all_users():
    users = []
    cursor = db.users.find({})
    
    for user in  cursor.to_list(length=100):
        # Manually convert ObjectId to string
        user["_id"] = str(user["_id"])
        users.append(user)
        
    return users


@router.post("/approve/{user_id}")
async def approve_user(user_id: str, admin = Depends(verify_admin)):
    result = db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"status": "active"}}
    )
    return {"success": result.modified_count > 0}