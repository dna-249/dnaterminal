from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from jose import jwt
import asyncio
import paramiko
import json
# In api/index.py
from api.auth import router as auth_router
# In api/index.py
from api.admin import router as admin_router
# In api/index.py
# from api.ssh import router as ssh_router
from api.auth import get_current_user 
from api.db import init_db

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    init_db()

# 1. API routes FIRST
app.include_router(auth_router, prefix="/api/auth")
# app.include_router(ssh_router, prefix="/api/ssh")

# 2. Static files LAST
# This acts as a fallback for everything else

# Initialize FastAPI

# Add a route for the root URL
@app.get("/")
async def serve_home():
    return FileResponse("public/home.html")

app.include_router(auth_router, prefix="/api/auth")
app.include_router(
    admin_router, 
    prefix="/api/admin", 
    dependencies=[Depends(get_current_user)] # Ensure only logged-in users hit these
)

# Example of usage:
@app.get("/admin/users")
async def list_users(current_user: str ):
    # Your logic here
    return {"message": "Success"}




# Configuration
SECRET_KEY = "your-very-secure-secret-key"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- Security Helper ---
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

# --- Authentication Routes ---
@app.post("/api/auth/login")
async def login():
    # Implement your logic to verify credentials against your DB here
    return {"access_token": "your_jwt_token", "token_type": "bearer"}

@app.post("/api/auth/signup")
async def signup():
    # Implement your logic to hash the password and save the new user here
    return {"message": "User registered successfully"}

# --- WebSocket Terminal Route ---
@app.websocket("/api/ssh-stream")
async def ssh_terminal_handler(websocket: WebSocket):
    await websocket.accept()
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_channel = None

    try:
        init_message = await websocket.receive_text()
        config = json.loads(init_message)
        
        hostname = config.get('hostname')
        username = config.get('username')
        password = config.get('password')
        port = int(config.get('port', 22))

        await websocket.send_text(f"Connecting to remote host {hostname}:{port} via SSH...\r\n")
        ssh.connect(hostname=hostname, username=username, password=password, port=port, timeout=10)
        
        ssh_channel = ssh.invoke_shell(term='xterm', width=100, height=30)
        ssh_channel.setblocking(False)
        await websocket.send_text("✔ Connection Established! Starting session...\r\n\r\n")

    except Exception as e:
        await websocket.send_text(f"\r\n[SSH Connection Failed: {str(e)}]\r\n")
        await websocket.close()
        return

    async def read_from_ssh():
        try:
            while ssh_channel and not ssh_channel.exit_status_ready():
                if ssh_channel.recv_ready():
                    data = ssh_channel.recv(4096)
                    await websocket.send_text(data.decode('utf-8', errors='ignore'))
                await asyncio.sleep(0.01)
        except Exception:
            pass

    read_task = asyncio.create_task(read_from_ssh())

    try:
        while True:
            message = await websocket.receive_text()
            if ssh_channel and ssh_channel.send_ready():
                ssh_channel.send(message.encode('utf-8'))
    except WebSocketDisconnect:
        print("User cleanly disconnected from active session loop.")
    finally:
        read_task.cancel()
        if ssh_channel:
            ssh_channel.close()
        ssh.close()

app.mount("/index.html", StaticFiles(directory="public", html=True), name="public")
