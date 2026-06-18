import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import paramiko

app = FastAPI()

@app.websocket("/api/ssh-stream")
async def ssh_terminal_handler(websocket: WebSocket):
    # Accept the incoming serverless WebSocket handshake
    await websocket.accept()
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_channel = None

    try:
        # 1. Receive the initial credential initialization configuration packet
        init_message = await websocket.receive_text()
        config = json.loads(init_message)
        
        hostname = config.get('hostname')
        username = config.get('username')
        password = config.get('password')
        port = int(config.get('port', 22))

        await websocket.send_text(f"Serverless connection routing to {hostname}:{port}...\r\n")

        # 2. Establish the SSH tunnel from Vercel's serverless edge node to the target machine
        ssh.connect(hostname=hostname, username=username, password=password, port=port, timeout=10)
        
        # 3. Create interactive pseudo-terminal window attributes
        ssh_channel = ssh.invoke_shell(term='xterm', width=100, height=30)
        ssh_channel.setblocking(False)
        await websocket.send_text("✔ Secure Session Engaged!\r\n\r\n")

    except Exception as e:
        await websocket.send_text(f"\r\n[Serverless Connection Failed: {str(e)}]\r\n")
        await websocket.close()
        return

    # Background pipeline stream reader task
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
        # Listen for keystrokes sent from Vercel's client-side user view
        while True:
            message = await websocket.receive_text()
            if ssh_channel and ssh_channel.send_ready():
                ssh_channel.send(message.encode('utf-8'))
    except WebSocketDisconnect:
        print("User disconnected from serverless instance.")
    finally:
        read_task.cancel()
        if ssh_channel:
            ssh_channel.close()
        ssh.close()