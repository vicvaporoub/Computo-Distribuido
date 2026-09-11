import socket as s
from threading import Thread, Lock

HOST1 = 'localhost' #ip del CLEINTE
PORT1 = 50001 

HOST2 = "127.0.0.1" #ip del servidor
PORT2 = 50002
clients = {}
servers = {}

BUFSIZ = 1024

ADDR1 = (HOST1, PORT1)
ADDR2 = (HOST2, PORT2)

MIDDLEWARE_clients = s.socket(s.AF_INET, s.SOCK_STREAM)
MIDDLEWARE_servers = s.socket(s.AF_INET, s.SOCK_STREAM)

MIDDLEWARE_clients.bind(ADDR1)
MIDDLEWARE_clients.listen()

MIDDLEWARE_servers.bind(ADDR2)
MIDDLEWARE_servers.listen()

clients_lock = Lock()
servers_lock = Lock()

def handle_client(client, client_address):
    while True:
        expression = client.recv(BUFSIZ)
        if not expression:
            with clients_lock: 
                # ningún otro thread puede ejecutar simultáneamente ningún otro bloque que use ese mismo servers_lock 
                # el del tendría que esperar a que termine el for de la funcion de broadcast para eliminar a ese cliente
                del clients[client_address]
            client.close()
            break
        broadcast_to_servers(expression)


def handle_server(server, server_address):

        while True:
            result = server.recv(BUFSIZ)
            if not result:
                with servers_lock:
                    del servers[server_address]
                    server.close()
                break
            broadcast_to_clients(result)


def accept_client_incoming_connections():
    """Sets up handling for incoming clients."""
    while True:
        client, client_address = MIDDLEWARE_clients.accept()
        print("%s:%s has connected." % client_address)
        clients[client_address] = client
        Thread(target=handle_client, args=(client, client_address)).start()


def accept_server_incoming_connections():
    """Sets up handling for incoming clients."""
    while True:
        server, server_address = MIDDLEWARE_servers.accept()
        print("%s:%s has connected." % server_address)
        
        servers[server_address] = server
        Thread(target=handle_server, args=(server, server_address)).start()

def broadcast_to_servers(msg):  # prefix is for name identification.
    """Broadcasts an expression to all the servers."""
    with servers_lock:
        destinatarios = list(servers.values()) #hacemos una copia antes de iterar sobre la lista 
        #para que si agregamos un nuevo servidor no tenemos que esperar a que el send() termine
    for sock in destinatarios:
        try:
            sock.send(bytes(msg))
        except:
            print("\nError enviando a un servidor desconectado")


def broadcast_to_clients(msg):  # prefix is for name identification.
    """Broadcasts an expression to all the clients."""
    with clients_lock:
        destinatarios = list(clients.values())
    for sock in destinatarios:
        try:
            sock.send(bytes(msg))
        except:
            print("\nError enviando a un cliente desconectado")

def main():
    Thread(target=accept_client_incoming_connections).start() #para crear un hilo nuevo
    Thread(target=accept_server_incoming_connections).start()
    print("Middleware esperando conexiones")

main()

