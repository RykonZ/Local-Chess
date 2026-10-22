import socket
import threading

class ChessNetwork:
    def __init__(self, is_host, ip='127.0.0.1', port=8080, on_msg=None):
        self.is_host = is_host
        self.on_msg = on_msg
        self.conn = None
        self.connected = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if is_host:
            self.sock.bind(('', port))
            self.sock.listen(1)
            threading.Thread(target=self.accept_connection, daemon=True).start()
        else:
            threading.Thread(target=self.connect_to_host, args=(ip, port), daemon=True).start()

    def connect_to_host(self, ip, port):
        try:
            self.sock.connect((ip, port))
            self.conn = self.sock
            self.connected = True
            if self.on_msg: self.on_msg("SYS:CONNECTED")
            self.receive_messages()
        except Exception:
            if self.on_msg: self.on_msg("ERROR:Connection Failed")

    def accept_connection(self):
        try:
            self.conn, addr = self.sock.accept()
            self.connected = True
            if self.on_msg: self.on_msg("SYS:CONNECTED")
            self.receive_messages()
        except Exception: pass

    def receive_messages(self):
        while self.connected:
            try:
                data = self.conn.recv(1024).decode()
                if not data: break
                for msg in data.split('\n'):
                    if msg and self.on_msg: self.on_msg(msg)
            except Exception: break
        self.connected = False
        if self.on_msg: self.on_msg("DISCONNECT:")

    def send_msg(self, msg):
        if self.conn and self.connected:
            try: self.conn.sendall((msg + '\n').encode())
            except Exception: self.connected = False

    def close(self):
        self.connected = False
        if self.conn:
            try: self.conn.close()
            except Exception: pass
        try: self.sock.close()
        except Exception: pass