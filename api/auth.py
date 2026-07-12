from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
import os
from api.db import create_user, get_user
import bcrypt
from dotenv import load_dotenv

# Load variables from .env file into the environment
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set")

ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

router = APIRouter()

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = 'admin'  # Default role is admin
    status: str = 'pending'  # Default status is pending

# Helper functions
def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    # Use timezone-aware UTC datetime
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    print(f"DEBUG: Received token: {token}") # Add this
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        print(f"DEBUG: JWT Error: {e}") # Add this
        raise HTTPException(status_code=401)
@router.post("/signup")
async def signup(user: UserCreate):
    if get_user(user.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    create_user(user.username, get_password_hash(user.password), user.role, user.status)
    return {"message": "User registered successfully"}

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        # Move all logic inside the try block
        user = get_user(form_data.username)
        
        if not user or not verify_password(form_data.password, user["password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Incorrect username or password"
            )
            
        return {
            "access_token": create_access_token({"sub": form_data.username}), 
            "token_type": "bearer"
        }
        
    except Exception as e:
        # This will now capture errors from get_user, verify_password, or the token creation
        print(f"DEBUG ERROR: {str(e)}") 
        raise HTTPException(status_code=500, detail=str(e))
    