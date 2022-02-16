import socket
import threading

username = input("Enter username: ")

client_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_send.connect(('127.0.0.1', 55557))
client_send.send(("REGISTER TOSEND " + username + "\n\n").encode('ascii'))
reply = client_send.recv(1024).decode('ascii')
if reply != ("REGISTERED TOSEND " + username + "\n\n"):
    print("> " + reply)
    exit()
else:
    print('> REGISTERED SEND SOCKET')

client_recv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_recv.connect(('127.0.0.1', 55557))
client_recv.send(("REGISTER TORECV " + username + "\n\n").encode('ascii'))
reply = client_recv.recv(1024).decode('ascii')
if reply != ("REGISTERED TORECV " + username + "\n\n"):
    print("> " + reply)
    exit()
else:
    print('> REGISTERED RECIEVE SOCKET')

def parseSend(s):
    try:
        assert s[0] == '@'
        recipient_name = s[1:s.index(' ')]
        message = s[s.index(' ')+1:]
        length = len(message)
        return ["SEND ", recipient_name, "\n", "Content-length: ", str(length),  "\n\n",  message]
    except:
        return ["ERROR"]

def parseRecv(s):
    try:
        assert s[:7] == 'FORWARD'
        assert s[7] == ' '
        sender_name = s[8:s.index('\n')]
        assert s[s.index('\n') + 1: s.index(':')] == 'Content-length'
        assert s[s.index(':') + 1] == ' '
        length = int(s[s.index(':')+2:s.find('\n', s.find('\n')+1)])
        msg = s[s.find('\n\n') + 2:]
        assert len(msg) == length
        return ["FORWARD ", sender_name, "\n", "Content-length: ", str(length), "\n\n", msg]
    except:
        return ["ERROR"]

def receive():
    while True:
        try:
            message = client_recv.recv(1024).decode('ascii')
        except:
            message = 'bye'
        if message == 'bye':
            client_recv.close()
            client_send.close()
            return
        parsed_msg = parseRecv(message)
        if parsed_msg[0] == 'ERROR':
            if message == "ERROR 104 Recieved ACK Incomplete\Incorrect\n\n":
                print('> Unable to respond correctly to messages recieved.')
            else:
                error = "ERROR 103 Header Incomplete\n\n"
                client_recv.send(error.encode('ascii'))
                print("> Recieved a faulty message.")
        else:
            sender_name = parsed_msg[1]
            confirmation = "RECIEVED " + sender_name + "\n\n"
            client_recv.send(confirmation.encode('ascii'))
            print(parsed_msg[1] + ": " + parsed_msg[6])

def write():
    while True:
        line = input()
        if line == 'bye':
            client_send.send('bye'.encode('ascii'))
            client_send.close()
            return
        parsed_line = parseSend(line)
        result = ''.join(parsed_line)
        if result == 'ERROR':
            print('> INPUT ERROR: Please type again.')
        else:
            try:
                client_send.send(result.encode('ascii'))
            except:
                print('> Server down.')
                client_send.close()
                client_recv.close()
                return
            confirmation = client_send.recv(1024).decode('ascii')
            if confirmation == "SENT " + parsed_line[1] + "\n\n":
                print('> Message sent to ' + parsed_line[1] + ".")
            else:
                print('> ' + confirmation)
                if confirmation == "ERROR 103 Header Incomplete\n\n":
                    print('> Closing sockets. Please register again.')
                    client_recv.close()
                    client_send.close()
                    return

receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()
