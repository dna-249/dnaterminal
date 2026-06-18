import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import paramiko

app = FastAPI()

# We removed app.mount and the "/" redirect completely.
# Vercel's edge network will handle serving the HTML page instead.

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