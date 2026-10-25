import socket as s
import sys
from threading import Thread, Lock
import json
import uuid
import time
HOST1 = 'localhost' #ip donde el nodo escuchará conexiones
ID_nodo =  str(uuid.uuid4())
clients = {}
servers = {}
nodes = {}
vistos = {}
TIEMPO_VISTOS = 60
PUERTO_DESCUBRIMIENTO = 50000
if len(sys.argv) < 2:
    print("Necesita ingresar un numero de puerto")
    sys.exit()
PORT1 = int(sys.argv[1])

ADDR1 = (HOST1, PORT1)# si fuera sys.argv[0] entonces retorna el nombre del script

Node_socket = s.socket(s.AF_INET, s.SOCK_STREAM)

Node_socket.bind(ADDR1)
Node_socket.listen()

clients_lock = Lock()
servers_lock = Lock()
nodes_lock = Lock()
vistos_lock = Lock()
def conectar_a_nodo(puerto, id_remoto):
    with nodes_lock:
        if id_remoto in nodes:
            return
    socket_client = s.socket(s.AF_INET, s.SOCK_STREAM)
    try:
        socket_client.connect((HOST1, puerto))
    except Exception as e:
        print(f"Ocurrió un error: {e}")
        socket_client.close()
        return
    dic = json.dumps({"tipo": "NODO", "id": ID_nodo}) + "\n"
    try:
        socket_client.sendall(dic.encode("utf-8"))
    except Exception as e:
        print(f"Ocurrió un error: {e}")
        socket_client.close()
        return
    with nodes_lock: 
        nodes[id_remoto] = socket_client
        print(f"Conexión a NODO[ID:{id_remoto[:8]}] en el puerto {puerto}")
    lector = socket_client.makefile("r", encoding="utf-8")
    Thread(target=atender, args=(lector, socket_client, "NODO", id_remoto)).start()
        
def escucha(): #UDP
    sock = s.socket(s.AF_INET, s.SOCK_DGRAM)
    sock.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR, 1)   # permite que VARIOS procesos usen el mismo puerto
    # sock.setsockopt(level, optname, value)
    # level Especifica a qué capa o nivel pertenece la opción 
    # (por ejemplo, socket.SOL_SOCKET para opciones generales del propio socket, o a nivel de protocolo como TCP/IP)
    # optname: El nombre de la opción específica que deseas modificar (por ejemplo, socket.SO_REUSEADDR)
    # value: El valor que quieres asignarle a esa opción (generalmente un número entero o una estructura de bytes
    
    # Al activar SO_REUSEADDR (poniéndole un 1), le estás diciendo al sistema operativo: "Oye, 
    # si apago mi programa y lo vuelvo a encender, 
    # déjame usar el mismo puerto inmediatamente. No me hagas esperar".
    # Y ademas Permite que múltiples programas independientes en la misma computadora 
    # se amarren exactamente al mismo puerto de red para recibir una transmisión conjunt0
    sock.bind(("", PUERTO_DESCUBRIMIENTO))     
    while True:
        datos, remitente = sock.recvfrom(1024)
        mensaje_recibido = datos.decode("utf-8")
        dic = json.loads(mensaje_recibido)
        if dic["id"] == ID_nodo:
            continue
        conectar_a_nodo(dic["Puerto"], dic["id"])

def anuncia(): #UDP
    sock = s.socket(s.AF_INET, s.SOCK_DGRAM)
    sock.setsockopt(s.SOL_SOCKET, s.SO_BROADCAST, 1)   # sin esto, el sistema rechaza enviar a broadcast
    tipo = "Anuncio_nodo"
    dic = json.dumps({'tipo': tipo, 'id': ID_nodo, 'Puerto': PORT1})

    sock.sendto(dic.encode("utf-8"), ("255.255.255.255", PUERTO_DESCUBRIMIENTO))

def atender(lector, con_socket, tipo, clave): #TCP
    while True:
        try:
            linea = lector.readline()
        except OSError:
            linea = ""
        if not linea:
            if tipo == "GUI":
                with clients_lock: 
                    # ningún otro thread puede ejecutar simultáneamente ningún otro bloque que use ese mismo servers_lock 
                    # el del tendría que esperar a que termine el for de la funcion de broadcast para eliminar a ese cliente
                    del clients[clave]
                    print(f"Se desconectó {tipo} con id {clave[:8]}")
                    con_socket.close()
                break
            if tipo == "SERVIDOR":
                with servers_lock: 
                    # ningún otro thread puede ejecutar simultáneamente ningún otro bloque que use ese mismo servers_lock 
                    # el del tendría que esperar a que termine el for de la funcion de broadcast para eliminar a ese cliente
                    del servers[clave]
                    print(f"Se desconectó {tipo} con id {clave[:8]}")
                    con_socket.close()
                break
            if tipo == "NODO":
                with nodes_lock: 
                    # ningún otro thread puede ejecutar simultáneamente ningún otro bloque que use ese mismo servers_lock 
                    # el del tendría que esperar a que termine el for de la funcion de broadcast para eliminar a ese cliente
                    del nodes[clave]
                    print(f"Se desconectó {tipo} con id {clave[:8]}")
                    con_socket.close()
                break
        else:
            dic = json.loads(linea)
            message_id = dic["ID_mensaje"]
            with vistos_lock:
                ahora = time.time()
                # a) olvidar los IDs viejos
                for id_v, hora in list(vistos.items()):
                    if ahora - hora > TIEMPO_VISTOS: #lleva más de 60 s anotado?
                        del vistos[id_v]
                # b) ¿ya lo vi?
                repetido = message_id in vistos
                # c) si es nuevo, anotarlo con la hora
                if not repetido:
                    vistos[message_id] = ahora
            if repetido:
                print(f"[{PORT1}] {dic['codigo_de_contenido']} {str(message_id)[:8]} de {clave[:8]}: ya visto, descartado")
                continue
            print(f"[{PORT1}] {dic['codigo_de_contenido']} {str(message_id)[:8]} de {clave[:8]}: nuevo, reenviando")
            difundir(linea, clave)
            



def handle_conn(con_socket, addr): #TCP
    with con_socket.makefile("r", encoding="utf-8") as archivo_presentacion:
        presentacion = archivo_presentacion.readline()
        # leo la presentación 1 vez por eso esta fuera del while
        dic = json.loads(presentacion)
        #lo hago diccionario
        if dic['tipo'] == "GUI":
            with clients_lock:
                clients[dic['id']] = con_socket
                print(f"Se conectó {dic['tipo']} con id {dic['id'][:8]}")

        if dic['tipo'] == "SERVIDOR":
            with servers_lock: 
                servers[dic['id']] = con_socket
                print(f"Se conectó {dic['tipo']} con id {dic['id'][:8]}")

        if dic['tipo'] == "NODO":
            with nodes_lock: 
                nodes[dic['id']] = con_socket
                print(f"Se conectó {dic['tipo']} con id {dic['id'][:8]}")
        atender(archivo_presentacion, con_socket, dic['tipo'], dic['id'])
        
def accept_incoming_connections():
    while True:
        con_socket, addr = Node_socket.accept()

        print("%s:%s has connected." % addr)

        #clients[client_address] = client
        Thread(target=handle_conn, args=(con_socket, addr)).start()

def difundir(linea, clave_origen):
    destinatarios = []
    with nodes_lock:
        for clave,valor in nodes.items():
            if clave == clave_origen:
                continue
            socket_node = valor
            destinatarios.append(socket_node)
    with clients_lock:
        for clave,valor in clients.items():
            if clave == clave_origen:
                continue
            socket_client = valor
            destinatarios.append(socket_client)
    with servers_lock:
        for clave,valor in servers.items():
            if clave == clave_origen:
                continue
            socket_servers = valor
            destinatarios.append(socket_servers)
    for sockets in destinatarios:
        try:
            sockets.sendall(linea.encode("utf-8"))
        except OSError as e:
            print(f"Ocurrió un error: {e}")
            sockets.close()

def main():
    Thread(target=accept_incoming_connections).start() #para crear un hilo nuevo
    Thread(target=escucha).start() #para crear un hilo nuevo
    anuncia()
    print("Nodo esperando conexiones")

main()

