import socket
import select
import time
import json

HOST = "0.0.0.0"
PORT = 5001

with open("masks.json", "r") as f:
    MASKS = json.load(f)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    s.setblocking(False)  # non-blocking
    print(f"Listening on {HOST}:{PORT}...")

    clients = []  # list of active client sockets

    while True:
        # Watch listening socket + all clients for readability
        readable, _, _ = select.select([s] + clients, [], [], 0.1)

        for sock in readable:
            if sock is s:
                # New connection
                conn, addr = s.accept()
                conn.setblocking(True)
                clients.append(conn)
                if not addr[0] in MASKS:
                    conn.send(b"GETMASK")
                    MASKS[addr[0]] = conn.recv(1024).decode()
                    with open("masks.json", "w") as f:
                        json.dump(MASKS, f, indent=2)
                else:
                    conn.send(MASKS[addr[0]].encode())
                print("New client:", addr, MASKS[addr[0]])
                conn.setblocking(False)
            else:
                # Data from existing client
                try:
                    data = sock.recv(1024)
                    if not data:
                        # Client disconnected
                        clients.remove(sock)
                        sock.close()
                        print("Client disconnected")
                    else:
                        if data == b"MSGS":
                            with open("chatLogs.txt", "r") as f:
                                for line in f.readlines():
                                    sock.sendall(line[line.find(']')+1:-1].encode().replace(b':', b'\x00') + b'\x01')
                            sock.sendall(b"END\x00\x01")
                        else:
                            print(MASKS[sock.getsockname()[0]] + ':', data.decode())
                            with open("chatLogs.txt", "a") as f:
                                if time.gmtime(time.time()).tm_hour >= 6:
                                    f.write(f"[{time.gmtime().tm_yday}:{time.gmtime().tm_hour - 6}:{time.gmtime().tm_min}:{time.gmtime().tm_sec}]{MASKS[sock.getsockname()[0]]}:{data.decode()}\n")
                                else:
                                    f.write(f"[{time.gmtime().tm_yday - 1}:{time.gmtime().tm_hour + 18}:{time.gmtime().tm_min}:{time.gmtime().tm_sec}]{MASKS[sock.getsockname()[0]]}:{data.decode()}\n")
                            for client in clients:
                                if client == sock:
                                    client.sendall(b"You" + b'\x00' + data + b'\x01')
                                else:
                                    client.sendall(MASKS[sock.getsockname()[0]].encode() + b'\x00' + data + b'\x01')
                except ConnectionResetError:
                    # Client reset the connection (abrupt disconnect)
                    print("Client disconnected (reset by peer)")
                    if sock in clients:
                        clients.remove(sock)
                    sock.close()
                except OSError as e:
                    # Any other socket-level error, treat as disconnect
                    print(f"Socket error, closing client: {e}")
                    if sock in clients:
                        clients.remove(sock)
                    sock.close()