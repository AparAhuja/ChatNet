import socket
import threading

host = '127.0.0.1'
port = 55557

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((host, port))
server.listen()

send_clients = {}
recv_clients = {}
send_client_names = {}
recv_client_names = {}

def broadcast(sender, message):
    cnt = 1
    for client in recv_clients.values():
        if(client != sender):
            client.send(message.encode('ascii'))
            reply_msg = client.recv(1024).decode('ascii')
            if reply_msg == "RECIEVED " + recv_client_names[sender] + "\n\n":
                cnt+=1
    return cnt == len(recv_clients)

def handle(client):
    while True:
        message = client.recv(1024).decode('ascii')
        if message == 'bye':
            sender_name = send_client_names[client]
            sender_send = client
            sender_recv = recv_clients[sender_name]
            sender_recv.send('bye'.encode('ascii'))
            send_clients.pop(sender_name)
            recv_clients.pop(sender_name)
            send_client_names.pop(sender_send)
            recv_client_names.pop(sender_recv)
            sender_recv.close()
            sender_send.close()
            return
        try:
            assert message[:4] == "SEND"
            assert message[4] == ' '
            assert message[message.index('\n') + 1:message.index(':')] == 'Content-length'
            assert message[message.index(':') + 1] == ' '
            assert message[5:message.index('\n')].isalnum()
            length = int(message[message.index(':') + 2:message.index('\n\n')])
            msg = message[message.index('\n\n')+2:]
            assert length == len(msg)
        except:
            fwd_msg = "ERROR 103 Header Incomplete\n\n"
            client.send(fwd_msg.encode('ascii'))
            sender_name = send_client_names[client]
            sender_send = client
            sender_recv = recv_clients[sender_name]
            send_clients.pop(sender_name)
            recv_clients.pop(sender_name)
            send_client_names.pop(sender_send)
            recv_client_names.pop(sender_recv)
            sender_recv.close()
            sender_send.close()
            return

        try:
            recipient_name = message[5:message.index('\n')]
            recipient_recv = 'ALL' if recipient_name =='ALL' else recv_clients[recipient_name]
            sender_name = send_client_names[client]
            sender_send = client

            fwd_msg = "FORWARD " + sender_name + message[message.index('\n'):]

            if recipient_name == "ALL":
                assert broadcast(recv_clients[sender_name], fwd_msg) == True
                fwd_msg = "SENT ALL\n\n"
                send_clients[sender_name].send(fwd_msg.encode('ascii'))
            else:
                recipient_recv.send(fwd_msg.encode('ascii'))
                reply_msg = recv_clients[recipient_name].recv(1024).decode('ascii')
                if reply_msg != "RECIEVED " + sender_name + "\n\n" and reply_msg != "ERROR 103 Header incomplete\n\n":
                    recv_clients[recipient_name].send("ERROR 104 Recieved ACK Incomplete\Incorrect\n\n".encode('ascii'))
                assert reply_msg == "RECIEVED " + sender_name + "\n\n"
                fwd_msg = "SENT " + recipient_name + "\n\n"
                send_clients[sender_name].send(fwd_msg.encode('ascii'))
        except:
            fwd_msg = "ERROR 102 Unable to send\n\n"
            send_clients[sender_name].send(fwd_msg.encode('ascii'))

def receive():
    while True:
        client, address = server.accept()
        join_req = client.recv(1024).decode('ascii')
        if join_req[:15] == "REGISTER TOSEND":
            username = join_req[16: -2]
            if username in send_clients.keys() or username == 'ALL':
                client.send("ERROR 200 Username already taken\n\n".encode('ascii'))
            elif username.isalnum():
                send_clients[username] = client
                send_client_names[client] = username
                client.send(("REGISTERED TOSEND" + join_req[15:]).encode('ascii'))
                thread = threading.Thread(target=handle, args=(client,))
                thread.start()
            else:
                client.send("ERROR 100 Malformed username\n\n".encode('ascii'))
        elif join_req[:15] == "REGISTER TORECV":
            username = join_req[16: -2]
            if username in recv_clients.keys() or username == 'ALL':
                client.send("ERROR 200 Username already taken\n\n".encode('ascii'))
            elif username.isalnum():
                recv_clients[username] = client
                recv_client_names[client] = username
                client.send(("REGISTERED TORECV" + join_req[15:]).encode('ascii'))
            else:
                client.send("ERROR 100 Malformed username\n\n".encode('ascii'))
        else:
            client.send("ERROR 101 No user registered\n\n".encode('ascii'))

receive()

