import threading, socket, json, locale, time, os, curses
from ChatInterface import ChatInterface

locale.setlocale(locale.LC_ALL, '')

class Client:
    def __init__(self, host, port, username):
        self.host = host
        self.port = port # Port to listen on
        self.username = username


        self.receiver = Receiver(self.host, self.port, self)
        self.senders = []

        self.ctx: ChatInterface = ChatInterface(username)
        self.ctx.clear()
        
        self.loop_thread = threading.Thread(target=self.loop)

        self.connections: [Connection] = [Connection(0, self.username, (self.host, self.port))]
        self.id = 0
    
    def start_loop(self):
        self.loop_thread.start()
    
    def loop(self):
        while True:
            # TODO: Add commands here
            msg = self.ctx.loop()

            if msg.startswith('/'):
                self.ctx.clear_last_line()
                if msg == '/help':
                    self.ctx.write_message_no_prompt("Commands:")
                    self.ctx.write_message_no_prompt("/help - Displays this message")
                    self.ctx.write_message_no_prompt("/exit - Exits the program")
                    self.ctx.write_message_no_prompt("/list - Lists all connected clients")
                    self.ctx.write_message_no_prompt("/username <username> - Changes your username")
                    self.ctx.write_message("/msg <user> <message> - Sends a private message to a user")
                    continue
                elif msg == '/exit':
                    self.ctx.write_message("Exiting...")
                    self.send(f"DISCONNECT-{self.id}-{self.id}\r\n".encode("utf-16"))
                    os._exit(0)
                    break
                elif msg == '/list':
                    self.ctx.write_message("Connected users:")
                    for connection in self.connections:
                        self.ctx.write_message(f" - {connection.username} [{connection.id}]")
                    continue
                elif msg.startswith('/username'):
                    self.set_username(msg.split(" ")[1])
                    self.send(f"UPDATE-{self.id}-{self.id}-{self.username}\r\n".encode("utf-16"))
                    self.ctx.write_message(f"You changed your username to {self.username}!", curses.color_pair(4))
                    continue
                elif msg.startswith('/msg'):
                    username = msg.split(" ")[1]
                    msg = " ".join(msg.split(" ")[2:])
                    connection = self.get_connection_by_username(username)
                    if connection == None:
                        self.ctx.write_message(f"User not found!", curses.color_pair(2))
                        continue

                    if connection.id == self.id:
                        self.ctx.write_message(f"You cannot send a private message to yourself!", curses.color_pair(2))
                        continue
                    
                    sender = Sender(connection.addr[0], connection.addr[1], connection.id, self)
                    sender.connect()
                    sender.send(f"PMSG-{self.id}-{msg}\r\n".encode('utf-16'))
                    self.ctx.write_message(f"You -> {username} (private): {msg}", curses.color_pair(5))
                    # TODO
                    continue

            self.send(f"MSG-{self.id}-{self.id}-{msg}\r\n".encode('utf-16'))
    
    def connect(self, addr):
        sender = Sender(addr[0], addr[1], 0, self)
        sender.connect()
        sender.send(f"CONNECT-{self.port}\r\n".encode("utf-16"))
        self.senders.append(sender)
    
    def get_sender(self, addr):
        for sender in self.senders:
            if sender.addr == addr:
                return sender
        return None

    def send(self, data):
        for sender in self.senders:
            sender.send(data)
    
    def add_connection(self, connection):
        for conn in self.connections:
            if conn.addr == connection.addr:
                return
        self.connections.append(connection)
        self.connections.sort(key=lambda x: x.id)
    
    def remove_connection(self, id):
        connection = self.get_connection(id)
        
        self.connections.remove(connection)
        self.reassign_ids()

    def get_connection(self, id):
        for connection in self.connections:
            if connection.id == id:
                return connection
        return None

    def get_connection_by_username(self, username):
        for connection in self.connections:
            if connection.username == username:
                return connection
        return None

    def reassign_ids(self):
        self.connections.sort(key=lambda x: x.id)
        for i in range(len(self.connections)):
            if self.connections[i].addr == (self.host, self.port):
                self.id = i
            self.connections[i].id = i
        
        for sender in self.senders:
            sender.close()

        # Update senders
        self.senders = []
        for connection in self.connections:
            if connection.id == self.id + 1 or connection.id == self.id - 1:
                sender = Sender(connection.addr[0], connection.addr[1], connection.id, self)
                sender.connect()
                sender.start_ping_loop()
                self.senders.append(sender)
    
    def send_to_all(self, data, exclude_id=None):
        for connection in self.connections:
            if connection.id == exclude_id:
                continue
            sender = self.get_sender(connection.addr)
            if sender == None:
                continue
            sender.send(data)
    
    def forward_message(self, data, from_id=None):
        from_conn = self.get_connection(from_id)
        if from_conn == None and from_id != None:
            return
        for sender in self.senders:
            if sender.id == from_id and from_id != None:
                continue
            sender.send(data)
    
    def set_username(self, username):
        self.username = username
        self.ctx.username = username
        self.get_connection(self.id).username = username
        
        


class Receiver:
    def __init__(self, host, port, client):
        self.host = host
        self.port = port

        self.client = client

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)

        self.listen_thread = threading.Thread(target=self.listen)
    
    def start(self):
        self.listen_thread.start()
        self.client.ctx.write_message(f"Listening on {self.host}:{self.port}", curses.color_pair(4))
    
    def listen(self):
        
        while True:
            conn, addr = self.socket.accept()
            # print(f"Connection from {addr}")
            thread = threading.Thread(target=self.handle_conn, args=(conn,))
            thread.start()
    
    def handle_conn(self, conn):
        while True:
            try:
                data: bytes = conn.recv(1024)
            except:
                break
            if not data:
                break

            # print(data.decode('utf-16'))
            # self.client.ctx.write_message(f"Received {data.decode('utf-16')} from {conn.getpeername()}")

            data = data.decode('utf-16')
            messages = data.split("\r\n")
            for message in messages:
                if message == "":
                    continue

                data = message

                if data.startswith("JOIN"):
                    # JOIN-<FORWARDER_ID>-<PORT>-<ID>-<USERNAME>

                    forwarder_id = int(data.split("-")[1])
                    port = data.split("-")[2]
                    id = int(data.split("-")[3])
                    username = "-".join(data.split("-")[4:])

                    self.client.add_connection(
                        Connection(id, username, (conn.getpeername()[0], int(port)))
                    )

                    self.client.reassign_ids()

                    self.client.ctx.write_message(f"{username} has joined the chat!", curses.color_pair(4))

                    # Send the message along to the other clients
                    # TODO: use utf-16 instead
                    new_payload = f"JOIN-{self.client.id}-{port}-{id}-{username}\r\n".encode("utf-16")
                    self.client.forward_message(new_payload, forwarder_id)
                    
                    continue
                elif data.startswith("MSG"):
                    # MSG-<FORWARDER_ID>-<ID>-<MESSAGE>
                    # Where ID is the ID of the client that originally sent the message
                    # and FORWARDER_ID is the ID of the client that forwarded the message.
                    # This is to prevent infinite loops

                    id = int(data.split("-")[2])
                    forwarder_id = int(data.split("-")[1])
                    msg = '-'.join(data.split("-")[3:])
                    

                    connection = self.client.get_connection(int(id))
                    if connection == None:
                        continue

                    self.client.ctx.write_message(f"{connection.username}: {msg}")
                    
                    # TODO: use utf-16 instead
                    new_payload = f"MSG-{self.client.id}-{id}-{msg}\r\n".encode("utf-16")
                    self.client.forward_message(new_payload, forwarder_id)

                    continue
                elif data.startswith("PMSG"):
                    # MSGP-<ID>-<MESSAGE>
                    # Private message

                    id = int(data.split("-")[1])
                    msg = '-'.join(data.split("-")[2:])

                    connection = self.client.get_connection(int(id))
                    if connection == None:
                        continue
                        
                    self.client.ctx.write_message(f"{connection.username} -> You (private): {msg}", curses.color_pair(5))
                    continue
                elif data.startswith("CONNECT"):
                    # CONNECT-<PORT>
                    # Used to get the ID and all clients that are connected to the network.
                    # Response: ID0x2D<ID>0x2D<JSON> (see below)
                    port = data.split("-")[1]
                    self.client.id += 1
                    self.client.get_connection(self.client.id-1).id = self.client.id
                    
                    # Send the ID back
                    sender = Sender(conn.getpeername()[0], int(port), 0, self.client)
                    sender.connect()

                    clients = []
                    for connection in self.client.connections:
                        clients.append({
                            "id": connection.id,
                            "username": connection.username,
                            "host": connection.addr[0],
                            "port": connection.addr[1]
                        })
                    
                    sender.send(f"ID-{self.client.id - 1}-{json.dumps(clients)}\r\n".encode("utf-16"))

                    # Send update with new ID to all clients
                    self.client.send(f"UPDATE-{self.client.id - 1}-{self.client.id}-{self.client.username}\r\n".encode("utf-16"))

                    continue
                elif data.startswith("ID"):
                    # ID0x2D<ID>0x2D<JSON>
                    # Sent by the server to the client that sent the CONNECT message.
                    # The ID is the ID of the client that received the message.
                    # Send a JOIN message to the client
                    # The JSON data is a list of clients connected to the network.
                    # Format: [{"id": 0, "username": "username", "host": "host", "port": 1234}, ...]

                    id = data.split("-")[1]
                    self.client.get_connection(self.client.id).id = int(id)
                    self.client.id = int(id)

                    clients = data.split("-")[2]
                    clients = json.loads(clients)
                    for client in clients:
                        # self.client.ctx.write_message(f"Client: {client}")
                        self.client.add_connection(
                            Connection(int(client["id"]), client["username"], (client["host"], client["port"]))
                        )
                    
                    
                    
                    
                    # Update senders
                    self.client.senders = []

                    for connection in self.client.connections:
                        if self.client.get_sender(connection.addr) != None:
                            continue
                        if connection.id == self.client.id + 1 or connection.id == self.client.id - 1:
                            sender = Sender(connection.addr[0], connection.addr[1], connection.id, self.client)
                            sender.connect()
                            sender.start_ping_loop()
                            self.client.senders.append(sender)

                    
                    self.client.ctx.write_message(f"You joined the chat!", curses.color_pair(4))
                    self.client.ctx.write_message(f"Connected users: {', '.join([f'{connection.username} (You)' if connection.id == self.client.id else connection.username for connection in self.client.connections])}", curses.color_pair(4))


                    for sender in self.client.senders:
                        sender.send(f"JOIN-{int(id)}-{self.client.port}-{int(id)}-{self.client.username}\r\n".encode("utf-16"))


                    continue
                elif data.startswith("UPDATE"):
                    # UPDATE-<OLD_ID>-<NEW_ID>-<USERNAME>
                    old_id = int(data.split("-")[1])
                    new_id = int(data.split("-")[2])
                    username = "-".join(data.split("-")[3:])

                    connection = self.client.get_connection(old_id)
                    if connection == None:
                        continue

                    # If the username has changed
                    if connection.username != username:
                        self.client.ctx.write_message(f"{connection.username} has changed their username to {username}!", curses.color_pair(4))

                    connection.id = new_id
                    if username != "":
                        connection.username = username

                    # forward message to the rest of the clients
                    self.client.forward_message(data, new_id)
                    continue
                elif data.startswith("DISCONNECT"):
                    # DISCONNECT-<FORWARDER_ID>-<ID>
                    # Where ID is the ID of the client that disconnected

                    id = int(data.split("-")[2])
                    forwarder_id = int(data.split("-")[1])

                    connection = self.client.get_connection(id)
                    if connection == None:
                        continue

                    if connection.id == self.client.id:
                        os._exit(0)

                    self.client.ctx.write_message(f"{connection.username} has left the chat!", curses.color_pair(4))

                    self.client.remove_connection(id)

                    # forward message to the rest of the clients
                    self.client.forward_message(data, forwarder_id)
                elif data.startswith("PLING"):
                    # PLING-<FROM_ID>-<TO_ID>

                    from_id = int(data.split("-")[1])
                    to_id = int(data.split("-")[2])

                    if to_id != self.client.id:
                        continue

                    if self.client.get_connection(from_id) == None:
                        continue

                    # Send a PLONG message back
                    sender = self.client.get_sender(self.client.get_connection(from_id).addr)
                    if sender == None:
                        continue

                    sender.send(f"PLONG-{self.client.id}-{from_id}\r\n".encode("utf-16"))
                    continue
                elif data.startswith("PLONG"):
                    # PLONG-<FROM_ID>-<TO_ID>

                    from_id = int(data.split("-")[1])
                    to_id = int(data.split("-")[2])

                    if to_id != self.client.id:
                        continue

                    sender = self.client.get_sender(self.client.get_connection(from_id).addr)
                    if sender == None:
                        continue

                    sender.handle_pong()
                    continue



        conn.close()
        

class Sender:
    def __init__(self, host, port, id, client: Client, **kwargs):
        self.addr = (host, port)
        self.id = id

        self.client = client

        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.stop_thread = False
    
    def connect(self):
        self.conn.connect(self.addr)
    
    def start_ping_loop(self):
        self.last_pong_time = time.time()
        self.ping_thread = threading.Thread(target=self.ping_loop, args=(lambda: self.stop_thread,))
        self.ping_thread.start()

    def send(self, data):
        try:
            self.conn.sendall(data)
        except:
            # oopsie
            pass
    
    def close(self):
        self.stop_thread = True
        self.conn.close() 


    def __repr__(self):
        return f"Sender({self.addr}, {self.id})"

    def ping_loop(self, stop):
        while True:
            time.sleep(1)
            self.send(f"PLING-{self.client.id}-{self.id}\r\n".encode("utf-16"))
            if time.time() - self.last_pong_time > 5:
                # Send DISCONNECT message
                self.client.send(f"DISCONNECT-{self.client.id}-{self.id}\r\n".encode("utf-16"))

                connection = self.client.get_connection(self.id)
                if connection == None:
                    continue

                self.client.ctx.write_message(f"{connection.username} has left the chat!", curses.color_pair(4))

                self.client.remove_connection(self.id)

                break

            if stop():
                break
    
    def handle_pong(self):
        self.last_pong_time = time.time()
    
    

class Connection:

    def __init__(self, id, username, addr):
        self.id = id
        self.username = username
        self.addr = addr

    def __repr__(self):
        return f"Connection({self.id}, {self.username}, {self.addr})"