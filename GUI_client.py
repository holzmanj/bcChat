import tkinter
import socket
from threading import Thread
import time
import traceback

USER_NAME = 'user'
HOST = ''
PORT = 9069
sock = None
connected = False
connection_thread = None


# Attempts to connect to connect to host and starts new thread on success
def connect_to_server():
    global connected, sock, connection_thread, cipher
    if connected:
        disconnect_from_server()
        time.sleep(1)
    try:
        # Create new socket and connect
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        sock.connect((HOST, PORT))
        append_to_log('\tConnected to %s\n' % HOST)
        sock.send(bytes('/name %s' % USER_NAME, encoding='UTF-8'))
        connected = True
        # Start listening to server in separate thread
        connection_thread = Thread(target=listen_to_server)
        connection_thread.start()
    except:
        append_to_log('\tConnection failed.\n')
        traceback.print_exc()


# Disconnects from currently connected server
def disconnect_from_server():
    global connected
    if connected:
        connected = False
    else:
        append_to_log('\tYou are not connected to a server.\n')


# Adds message to chat log sans newline
def append_to_log(msg):
    log.configure(state='normal')
    log.insert('end', msg)
    log.configure(state='disabled')
    log.see(tkinter.END)


# Sends user message to server (or redirects to command handling if appropriate)
def send_message(event):
    msg = user_input.get()

    # Client-side commands indicated by '/' prefix
    if msg[0] == '/':
        append_to_log(msg + '\n')
        handle_command(msg[1:])
        user_input.delete(0, len(msg))
        return

    msg = bytes('[' + USER_NAME + '] ' + msg + '\n', encoding='UTF-8')

    if connected:
        sock.send(msg)
    else:
        append_to_log(msg)

    user_input.delete(0, len(msg))


# Sends private message to single user on server
def send_whisper(user, message):
    if connected:
        message = message.split(None, 2)[2]
        sock.send(bytes('/whisper %s %s' % (user, message), encoding='UTF-8'))
    else:
        append_to_log('\tYou are not connected to a server.\n')


# Changes the user's display name
def change_name(name):
    global USER_NAME
    if len(name) < 20:
        USER_NAME = name
        if connected:
            sock.send(bytes('/name %s' % name, encoding='UTF-8'))
        else:
            append_to_log('\tDisplay name changed to \"%s\"\n' % name)
    else:
        append_to_log('\tName too long.  Max 20 characters.\n')


# Gets list of currently connected users from server
def get_users():
    if connected:
        sock.send(bytes('/getusers', encoding='UTF-8'))
    else:
        append_to_log('\tYou are not connected to a server.\n')


# Parses client-side commands
def handle_command(command):
    global HOST, connected

    args = command.split()
    if args[0] == 'help':
        if len(args) == 1:
            append_to_log('\tFor details about a specific commend, enter /help <command>\n'
                          '\tAvailable commands:\n'
                          '\t\t/connect\n'
                          '\t\t/disconnect\n'
                          '\t\t/name\n'
                          '\t\t/whisper\n')
        else:
            if args[1] == 'connect':
                append_to_log('\t/connect <hostname> - creates connection to specified server.\n')
            elif args[1] == 'disconnect':
                append_to_log('\t/disconnect - breaks connection to current server.\n')
            elif args[1] == 'name':
                append_to_log('\t/name <name> - sets new display name for user.\n')
            else:
                append_to_log('\tUnknown command: %s\nRefer to /help for a list of commands.\n' % args[0])
    elif args[0] == 'connect':
        if len(args) > 1:
            HOST = args[1]
            connect_to_server()
        else:
            append_to_log('\tIncorrect format.  Refer to /help for assistance.\n')
    elif args[0] == 'disconnect':
        disconnect_from_server()
    # Changes user display name
    elif args[0] == 'name':
        if len(args) > 1:
            change_name(args[1])
        else:
            append_to_log('\tIncorrect format.  Refer to /help for assistance.\n')
    # Gets list of users connected to server
    elif args[0] == 'getusers':
        get_users()
    # Sends private message to a single user
    elif args[0] == 'whisper':
        if len(args) > 2:
            send_whisper(args[1], command)
        else:
            append_to_log('\tIncorrect format.  Refer to /help for assistance.\n')
    else:
        append_to_log('\tUnknown command: %s\nRefer to /help for a list of commands.\n' % args[0])


# Receives messages from server
def listen_to_server():
    global connected
    while connected:
        try:
            data = sock.recv(1024)
            if not data:
                append_to_log('\tServer has disconnected\n')
                connected = False
            else:
                append_to_log(data.decode(encoding='UTF-8'))
        except socket.timeout:
            continue
    append_to_log('\tDisconnecting from server %s\n' % sock.getpeername()[0])
    sock.close()


# Called on window close to kill
def on_exit():
    if connected:
        disconnect_from_server()
    root.destroy()

# TKINTER VARIABLES
root = tkinter.Tk()
root.minsize(200, 300)
root.bind('<Return>', send_message)
root.protocol('WM_DELETE_WINDOW', on_exit)


# Chat log
log = tkinter.Text(root, state='disabled', height=15, bg='#0a0909', fg='#ffffff', relief=tkinter.FLAT,
                   font=('Consolas', 10), tabs=20, wrap=tkinter.WORD)
log.pack(expand=True, fill=tkinter.BOTH)

# Text field for entering messages
user_input = tkinter.Entry(root, exportselection=0, width=100, relief=tkinter.FLAT, bd=5, bg='#161416', fg='#ffffff',
                           insertwidth=1, font=('Consolas', 10), insertbackground='#ffffff')
user_input.pack(side=tkinter.BOTTOM, fill=tkinter.X)

root.mainloop()
