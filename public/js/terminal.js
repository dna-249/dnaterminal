// Ensure Auth is available
// <script src="js/auth.js"></script>

const TerminalManager = {
    term: null,
    socket: null,

    init: (host,user,pass,port,containerId) => {
        // 1. Initialize xterm.js
        TerminalManager.term = new Terminal({
            cursorBlink: true,
            theme: { background: '#000000', foreground: '#f8fafc' },
            fontSize: 14
        });
        TerminalManager.term.open(document.getElementById(containerId));

        // 2. Connect to WebSocket with JWT
        const token = Auth.getToken();
        const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
        const wsUrl = `${protocol}${window.location.host}/api/ssh/stream?token=${token}`;
        
        TerminalManager.socket = new WebSocket(wsUrl);

        // 3. Handle Events
        TerminalManager.socket.onopen = () => {
            TerminalManager.term.writeln('\x1b[1;32mConnected to secure tunnel.\x1b[0m');
            // Send initial connection config (replace with actual UI inputs later)
            const config = { hostname: host, username: user, password: pass, port: port};
            console.log(config)
            TerminalManager.socket.send(JSON.stringify(config));
        };

        TerminalManager.socket.onmessage = (e) => {
            TerminalManager.term.write(e.data);
        };

        TerminalManager.term.onData((data) => {
            if (TerminalManager.socket.readyState === WebSocket.OPEN) {
                TerminalManager.socket.send(data);
            }
        });

        TerminalManager.socket.onclose = () => {
            TerminalManager.term.writeln('\r\n\x1b[1;31mSession Disconnected.\x1b[0m');
        };
    }
};