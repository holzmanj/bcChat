import tkinter
import socket
from threading import Thread
import time
import traceback
import configparser
import os

USER_NAME = 'user'
USER_COLOR = '#ffffff'
HOST = ''
PORT = 9069
sock = None
connected = False
connection_thread = None
CONNECTED_USERS = {}


# Attempts to connect to host and starts new thread on success
def connect_to_server():
    global connected, sock, connection_thread
    if connected:
        disconnect_from_server()
        time.sleep(1)
    try:
        # Create new socket and connect
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        sock.connect((HOST, PORT))
        append_to_log('Connected to %s\n' % HOST)
        sock.send(bytes('/name %s\n' % USER_NAME, encoding='UTF-8'))
        sock.send(bytes('/color %s' % USER_COLOR, encoding='UTF-8'))
        connected = True
        # Start listening to server in separate thread
        connection_thread = Thread(target=listen_to_server)
        connection_thread.start()
    except:
        append_to_log('Connection failed.\n')
        traceback.print_exc()


# Disconnects from currently connected server
def disconnect_from_server():
    global connected
    if connected:
        connected = False
    else:
        append_to_log('You are not connected to a server.\n')


# Handles data received from server about connected users
def parse_user_info(user_info):
    end = 0
    while user_info.find('[', end) != -1:
        start = user_info.find('[', end) + 1
        comma = user_info.find(',', start)
        address = user_info[start:comma]

        start = comma + 1
        comma = user_info.find(',', start)
        name = user_info[start:comma]

        start = comma + 1
        end = user_info.find(']', start)
        color = user_info[start:end]

        CONNECTED_USERS[address] = (name, color)
        log.tag_configure(address, foreground=color)


# Adds message to chat log sans newline
def append_to_log(msg):
    log.configure(state='normal')
    # Color user names
    if msg[0] == '[':
        index = msg.find(' ')
        name = msg[0:index]
        msg = msg[index:]
        log.insert('end', name, 'user') # add multiple colors
        log.insert('end', msg)
    else:
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
        append_to_log(msg.decode('UTF-8'))

    user_input.delete(0, len(msg))


# Sends private message to single user on server
def send_whisper(user, message):
    if connected:
        message = message.split(None, 2)[2]
        sock.send(bytes('/whisper %s %s' % (user, message), encoding='UTF-8'))
    else:
        append_to_log('You are not connected to a server.\n')


# Changes the user's display name
def change_name(name):
    global USER_NAME
    if len(name) < 20:
        USER_NAME = name
        if connected:
            sock.send(bytes('/name %s' % name, encoding='UTF-8'))
        else:
            append_to_log('Display name changed to \"%s\"\n' % name)
    else:
        append_to_log('Name too long.  Max 20 characters.\n')


# Changes color of user's display name
def change_color(color):
    global USER_COLOR
    if len(color) == 6:
        try:
            int(color, 16)  # throws exception if color is not in hex form
            USER_COLOR = '#%s' % color
            sock.send(bytes('/color %s' % USER_COLOR, encoding='UTF-8'))
        except:
            append_to_log('Incorrect format, make sure your color is in hex-code form.\n')
    elif len(color) == 7 and color[0] == '#':
        try:
            int(color[1:], 16)  # throws exception if color is not in hex form
            USER_COLOR = color
            sock.send(bytes('/color %s' % USER_COLOR, encoding='UTF-8'))
        except:
            append_to_log('Incorrect format, make sure your color is in hex-code form.\n')
    else:
        append_to_log('Incorrect format, make sure your color is in hex-code form.\n')
    log.tag_config('user', foreground=USER_COLOR)


# Gets list of currently connected users from server
def get_users():
    if connected:
        sock.send(bytes('/getusers', encoding='UTF-8'))
    else:
        append_to_log('You are not connected to a server.\n')


# Parses client-side commands
def handle_command(command):
    global HOST, connected

    args = command.split()
    if args[0] == 'help':
        if len(args) == 1:
            append_to_log('For details about a specific command, enter /help <command>\n'
                          'Available commands:\n'
                          '\t/connect\n'
                          '\t/disconnect\n'
                          '\t/getusers\n'
                          '\t/name\n'
                          '\t/color\n'
                          '\t/whisper\n')
        else:
            if args[1] == 'connect':
                append_to_log('\t/connect <hostname> - creates connection to specified server.\n')
            elif args[1] == 'disconnect':
                append_to_log('\t/disconnect - breaks connection to current server.\n')
            elif args[1] == 'name':
                append_to_log('\t/name <name> - sets new display name for user.\n')
            elif args[1] == 'color':
                append_to_log('\t/color <hexcode> - sets color for display name.\n')
            elif args[1] == 'getusers':
                append_to_log('\t/getusers - gets list of all currently connected users on a server.\n')
            elif args[1] == 'whisper':
                append_to_log('\t/whisper <user> <message> - sends a private message to another user.\n')
            else:
                append_to_log('Unknown command: %s\nRefer to /help for a list of commands.\n' % args[0])
    elif args[0] == 'connect':
        if len(args) > 1:
            HOST = args[1]
            connect_to_server()
        else:
            append_to_log('Incorrect format.  Refer to /help for assistance.\n')
    elif args[0] == 'disconnect':
        disconnect_from_server()
    # Changes user display name
    elif args[0] == 'name':
        if len(args) > 1:
            change_name(args[1])
        else:
            append_to_log('Incorrect format.  Refer to /help for assistance.\n')
    # Changes color of user display name
    elif args[0] == 'color':
        if len(args) > 1:
            change_color(args[1])
        else:
            append_to_log('Incorrect format.  Refer to /help for assistance.\n')
    # Gets list of users connected to server
    elif args[0] == 'getusers':
        get_users()
    # Sends private message to a single user
    elif args[0] == 'whisper':
        if len(args) > 2:
            send_whisper(args[1], command)
        else:
            append_to_log('Incorrect format.  Refer to /help for assistance.\n')
    else:
        append_to_log('Unknown command: %s\nRefer to /help for a list of commands.\n' % args[0])


# Receives messages from server
def listen_to_server():
    global connected
    while connected:
        try:
            data = sock.recv(1024)
            if not data:
                append_to_log('Server has disconnected\n')
                connected = False
            elif data[:9] == '/userinfo':
                parse_user_info(data)
            else:
                append_to_log(data.decode(encoding='UTF-8'))
        except socket.timeout:
            continue
    append_to_log('Disconnected from server %s\n' % sock.getpeername()[0])
    sock.close()


# Called on window close to kill
def on_exit():
    global config
    if connected:
        disconnect_from_server()
    config['DEFAULT']['displayname'] = USER_NAME
    config['DEFAULT']['port'] = str(PORT)
    config['DEFAULT']['color'] = USER_COLOR
    config.write(open('client.conf', 'w'))
    root.destroy()


# Parses default saved values from config file
config = configparser.ConfigParser()
if os.path.isfile('client.conf'):
    config.read('client.conf')
    USER_NAME = config.get('DEFAULT', 'displayname', fallback='user')
    PORT = int(config.get('DEFAULT', 'port', fallback=9069))
    USER_COLOR = config.get('DEFAULT', 'color', fallback='#ffffff')
else:
    config['DEFAULT'] = {'displayname': 'user', 'port': 9069, 'color': '#ffffff'}
    config.write(open('client.conf', 'w'))


# TKINTER VARIABLES
root = tkinter.Tk()
root.minsize(200, 300)
root.bind('<Return>', send_message)
root.protocol('WM_DELETE_WINDOW', on_exit)
root.iconbitmap('netrun.ico')
chat_title = '\uff2e\uff25\uff34\uff32\uff35\uff2e\uff0d\uff43\uff48\uff41\uff54'   # NETRUN-chat in full width chars
root.wm_title(chat_title)


# Chat log
log = tkinter.Text(root, state='disabled', height=15, bg='#0a0909', fg='#ffffff', relief=tkinter.FLAT,
                   font=('Consolas', 10), tabs=20, wrap=tkinter.WORD)
log.tag_configure('user', foreground=USER_COLOR)
log.pack(expand=True, fill=tkinter.BOTH)

# Text field for entering messages
user_input = tkinter.Entry(root, exportselection=0, width=100, relief=tkinter.FLAT, bd=5, bg='#161416', fg='#ffffff',
                           insertwidth=1, font=('Consolas', 10), insertbackground='#ffffff')
user_input.pack(side=tkinter.BOTTOM, fill=tkinter.X)
user_input.focus_set()

# Welcome message
append_to_log('welcome to %s\nenter \"/help\" if you don\'t know what to do.\n' % chat_title)

root.mainloop()
