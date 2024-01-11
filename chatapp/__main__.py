import client, socket, sys, curses
import network

def main():

    port = 9990 if len(sys.argv) <= 1 else int(sys.argv[1])
    local_mode = len(sys.argv) > 2 and sys.argv[2] == "local"

    client_ = client.Client(socket.gethostbyname(socket.gethostname()), port, "")
    
    username = client_.ctx.get_input("Enter a username: ")
    client_.set_username(username)

    client_.ctx.write_message_no_prompt("Finding clients on the network...", curses.color_pair(4))
    clients = network.find_client("192.168.195.0/24" if not local_mode else f"{socket.gethostbyname(socket.gethostname())}/36", (9990, 9994))

    if len(clients) > 0:
        client_.ctx.write_message_no_prompt("Found client, connecting...")
        client_.connect(clients[0])
    
    client_.ctx.clear()
    client_.ctx.write_message("Welcome to the chat client!", curses.color_pair(4))
    client_.ctx.write_message("Type '/help' for a list of commands.", curses.color_pair(4))
    client_.ctx.write_message("Type '/exit' to exit.", curses.color_pair(4))

    if len(clients) == 0:
        client_.ctx.write_message("Failed to connect to the network. Restart the client to try again.", curses.color_pair(2))

    client_.receiver.start()
    client_.start_loop()
        



if __name__ == '__main__':
    main()