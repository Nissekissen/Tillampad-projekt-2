import client, socket, sys, curses
import network

def main():
    global client

    port = int(sys.argv[1])
    target = sys.argv[2] if len(sys.argv) > 2 else None
    # print(target)

    client_ = client.Client(socket.gethostbyname(socket.gethostname()), port, "")
    
    username = client_.ctx.get_input("Enter a username: ")
    client_.set_username(username)

    client_.ctx.write_message_no_prompt("Finding clients on the network...", curses.color_pair(4))
    clients = network.find_client("192.168.0.0/24" if target is None else target, (9989, 9999), None if target is None else 1)

    if len(clients) > 0:
        client_.ctx.write_message_no_prompt("Found client, connecting...")
        for i, client in enumerate(clients):
            # client_.ctx.write_message_no_prompt("Client: " + client[0] + ":" + str(client[1]))
            if client[1] != port:
                client_.connect(clients[i])
                break
    
    client_.ctx.clear()
    client_.ctx.write_message("Welcome to the chat client!", curses.color_pair(4))
    client_.ctx.write_message("Type '/help' for a list of commands.", curses.color_pair(4))
    client_.ctx.write_message("Type '/exit' to exit.", curses.color_pair(4))
    # client_.ctx.write_message("Amount of clients connected: " + str(len(clients)), curses.color_pair(4))

    if len(clients) == 0:
        client_.ctx.write_message("Failed to connect to the network. Restart the client to try again.", curses.color_pair(2))

    client_.receiver.start()
    client_.start_loop()
        



if __name__ == '__main__':
    main()