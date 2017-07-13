import sys
import socket
import select
from time import sleep

HOST = ''
SOCKET_LIST = []
RECV_BUFFER = 4096
PORT = 9069
USER_NAMES = {}


# Main loop
def chat_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(10)        # max 10 clients to a server

    SOCKET_LIST.append(server_socket)

    print("Chat server started on port %s" % str(PORT))

    while True:
        # get the list sockets which are ready to be read through select
        # 4th arg, time_out = 0 : poll and never block
        ready_to_read, ready_to_write, in_error = select.select(SOCKET_LIST, [], [], 0)

        for sock in ready_to_read:
            # New connection request received
            if sock == server_socket:
                sockfd, addr = server_socket.accept()
                SOCKET_LIST.append(sockfd)
                print('%s:%s has connected' % addr)
                USER_NAMES['%s:%s' % addr] = None

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
                            broadcast(server_socket, data)
                            print(data, end='')
                    else:
                        # remove broken socket
                        remove_client(sock, server_socket)
                except:
                    remove_client(sock, server_socket)
                    print('Exception:', sys.exc_info()[0])
                    sleep(0.1)
                    continue


# Parses server side commands
def handle_command(c_sock, s_sock, command):
    args = command.split()

    if args[0] == 'name':
        if USER_NAMES['%s:%s' % c_sock.getpeername()] is None:
            broadcast(s_sock, '%s has joined the server\n' % args[1])
        else:
            broadcast(s_sock, '%s changed his name to %s\n' % (USER_NAMES['%s:%s' % c_sock.getpeername()], args[1]))
        USER_NAMES['%s:%s' % c_sock.getpeername()] = args[1]


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


# Disconnects socket and removes data relevant to client
def remove_client(c_sock, s_sock):
    if c_sock in SOCKET_LIST:
        SOCKET_LIST.remove(c_sock)
    broadcast(s_sock, "%s has disconnected\n" % USER_NAMES['%s:%s' % c_sock.getpeername()])
    address = '%s:%s' % c_sock.getpeername()
    print("%s (%s) has disconnected" % (address, USER_NAMES[address]))
    c_sock.close()


if __name__ == "__main__":
    sys.exit(chat_server())
