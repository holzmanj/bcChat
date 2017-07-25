import sys
import socket
import select
from time import sleep
import traceback

HOST = ''
SOCKET_LIST = []
RECV_BUFFER = 4096
PORT = 9069
USER_NAMES = {}
USER_COLORS = {}


# Main loop
def chat_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(10)        # max 10 clients to a server

    SOCKET_LIST.append(server_socket)

    print("Server started on port %s" % str(PORT))

    while True:
        ready_to_read, _, _ = select.select(SOCKET_LIST, [], [], 0)

        for sock in ready_to_read:
            # New connection request received
            if sock == server_socket:
                sockfd, addr = server_socket.accept()
                SOCKET_LIST.append(sockfd)
                print('%s:%s has connected' % addr)
                USER_NAMES['%s:%s' % addr] = None
                USER_COLORS['%s:%s' % addr] = None
                send_user_info(sockfd, server_socket)
                broadcast(server_socket, '/userinfo [%s,user,#ffffff]' % addr)

            # Existing client sends message or disconnects
            else:
                try:
                    # retrieve data from socket
                    data = sock.recv(RECV_BUFFER).decode('UTF-8')
                    if data:
                        # handle special commands
                        if data[0] == '/':
                            handle_command(sock, server_socket, data[1:])
                        else:
                            # ensure user has a name on the server
                            if USER_NAMES['%s:%s' % sock.getpeername()] is None:
                                direct_message(sock, '\tYou cannot send messages without first changing your name.\n',
                                               server_socket)
                            else:
                                broadcast(server_socket, data)
                                print(data, end='')
                    else:
                        # remove broken socket
                        remove_client(sock, server_socket)
                except:
                    remove_client(sock, server_socket)
                    traceback.print_exc()
                    sleep(0.1)
                    continue


# Sends newly connected user info for rest of users on server
def send_user_info(c_sock, s_sock):
    info_string = '/userinfo '
    for addr in USER_NAMES:
        info_string += '[%s,%s,%s]' % (addr, USER_NAMES[addr], USER_COLORS[addr])
    direct_message(c_sock, info_string, s_sock)


# Parses server side commands
def handle_command(c_sock, s_sock, command):
    args = command.split()

    if args[0] == 'name':
        change_name(args[1], c_sock, s_sock)
    elif args[0] == 'color':
        change_color(args[1], c_sock, s_sock)
    elif args[0] == 'getusers':
        user_list = ', '.join(USER_NAMES.values())
        direct_message(c_sock, '\tCurrently connected users: %s\n' % user_list, s_sock)
    elif args[0] == 'whisper':
        send_whisper(c_sock, s_sock, args[1], command.split(None, 2)[2])


# Allows user to change their display name
def change_name(name, c_sock, s_sock):
    # Checks for name collisions
    if name in USER_NAMES.values():
        direct_message(c_sock, '\tThere is already a user with the name \"%s\" on this server.\n' % name, s_sock)
        # Newly joined user
        if USER_NAMES['%s:%s' % c_sock.getpeername()] is None:
            direct_message(c_sock, '\tPlease set a new display name with \"/name <name>\"\n'
                                   '\tYou will not be able to send messages until you select a new name.\n', s_sock)
        return

    if USER_NAMES['%s:%s' % c_sock.getpeername()] is None:
        broadcast(s_sock, '%s has joined the server\n' % name)
    else:
        broadcast(s_sock, '%s changed his name to %s\n' % (USER_NAMES['%s:%s' % c_sock.getpeername()], name))
    USER_NAMES['%s:%s' % c_sock.getpeername()] = name


# Allows user to change the color of their display name
def change_color(color, c_sock, s_sock):
    if USER_COLORS['%s:%s' % c_sock.getpeername()] is not None:
        broadcast(s_sock, '%s changed his color\n' % USER_NAMES['%s:%s' % c_sock.getpeername()])
    USER_COLORS['%s:%s' % c_sock.getpeername()] = color
    print('%s changed his color' % USER_NAMES['%s:%s' % c_sock.getpeername()])


# Allows user to send direct message to another user
def send_whisper(c_sock, s_sock, user, message):
    if user in USER_NAMES.values():
        address = list(USER_NAMES.keys())[list(USER_NAMES.values()).index(user)]

        for u_sock in SOCKET_LIST:
            if u_sock != s_sock:
                if '%s:%s' % u_sock.getpeername() == address:
                    sender = USER_NAMES['%s:%s' % c_sock.getpeername()]
                    direct_message(u_sock, '{%s -> %s} %s\n' % (sender, user, message), s_sock)
                    direct_message(c_sock, '{%s -> %s} %s\n' % (sender, user, message), s_sock)
                    print('{%s -> %s} %s\n' % (sender, user, message))
    else:
        direct_message(c_sock, '\tThere is no user named \"%s\" on this server.\n' % user, s_sock)


# Send message to all clients
def broadcast(server_socket, message):
    message = bytes(message, encoding='UTF-8')
    for sock in SOCKET_LIST:
        # exclude self from broadcast
        if sock != server_socket:
            try:
                sock.send(message)
            except:
                # broken socket connection
                print('Connection to a client was broken.')
                remove_client(sock, server_socket)


# Send a message to a single connected client
def direct_message(c_sock, message, server_socket):
    message = bytes(message, encoding='UTF-8')
    try:
        c_sock.send(message)
    except:
        # broken socket connection
        print('Connection to a client was broken.')
        remove_client(c_sock, server_socket)


# Disconnects socket and removes data relevant to client
def remove_client(c_sock, s_sock):
    if c_sock in SOCKET_LIST:
        SOCKET_LIST.remove(c_sock)
    broadcast(s_sock, "%s has disconnected\n" % USER_NAMES['%s:%s' % c_sock.getpeername()])
    address = '%s:%s' % c_sock.getpeername()
    print("%s (%s) has disconnected" % (address, USER_NAMES[address]))
    USER_NAMES.pop(address, None)
    c_sock.close()


if __name__ == "__main__":
    sys.exit(chat_server())
