import socket as s
from threading import Lock
import json
import uuid
import sys

OPERACIONES = {"SUM": None, "SUB": None, "MUL": None, "DIV": None}

HOST1 = "127.0.0.1"

if len(sys.argv) < 3:
    print(f"Es necesario que especifique la operacion de la celula: {', '.join(OPERACIONES)} ")
    sys.exit()
OP = sys.argv[2].upper()
if OP not in OPERACIONES:
    print(f"Operación no válida. Opciones: {', '.join(OPERACIONES)}")
    sys.exit()

codigo_respuesta = f"{OP}_RES"
codigo_solicitud =f"{OP}_REQ"

PORT1 = int(sys.argv[1])

socket_server = s.socket(s.AF_INET, s.SOCK_STREAM)
socket_server.connect((HOST1, PORT1))

RUTA_ARCHIVO = f"results.txt"

file_lock = Lock()

id_unico = str(uuid.uuid4())




def openFile(expression, result):
    with file_lock:
        with open(RUTA_ARCHIVO, "a", encoding="utf-8") as file:
            file.write(f"Expresión: {expression} = {result} \n")


def send_presentation():
    tipo = "SERVIDOR"

    string = json.dumps({"tipo": tipo, "id": id_unico}) + "\n"
    print(string)
    try:
        socket_server.sendall(string.encode("utf-8"))
    except Exception as e:
        print(f"Ocurrió un error: {e}")

def recibir():
    lector = socket_server.makefile("r", encoding="utf-8")
    while True:
        try:
            linea = lector.readline()
        except OSError:
            linea = ""
        if not linea:
            print("El nodo cerró la conexión")
            socket_server.close()
            break
        dic = json.loads(linea)
        if dic['codigo_de_contenido'].endswith("_RES"):
            continue
        if dic["codigo_de_contenido"] != codigo_solicitud:
            print(f"IGNORADA {dic['codigo_de_contenido']} {dic['ID_celula_og'][:8]}")
            continue
        print(f"Atendiendo solicitud {dic['ID_mensaje']}: {dic['operandos']}")
        res = calculo(dic)
        responder(dic["ID_mensaje"], res)

        
def calculo(dic):
    operando1,operando2= dic["operandos"]
    id_mensaje = dic["ID_mensaje"]
    if OP == "SUM":
        resultado = operando1 + operando2
        print(f"Calculé {operando1} {OP} {operando2} = {resultado}")
    elif OP == "SUB":
        resultado = operando1 - operando2
        print(f"Calculé {operando1} {OP} {operando2} = {resultado}") 
    elif OP == "MUL":
        resultado = operando1 * operando2 
        print(f"Calculé {operando1} {OP} {operando2} = {resultado}")  
    elif OP == "DIV":
        try:
            resultado = operando1 / operando2
            print(f"Calculé {operando1} {OP} {operando2} = {resultado}")
        except ZeroDivisionError as e:
            print("No se puede dividir entre 0")
            resultado = "Error: división entre 0"
    return resultado

def responder(id_solicitud, resultado):
    id_mensaje = str(uuid.uuid4())
    dic_respuesta = {"ID_mensaje": id_mensaje, "ID_solicitud_original": id_solicitud, "codigo_de_contenido": codigo_respuesta, "resultado": resultado, "ID_celula_og": id_unico }
    respuesta = json.dumps(dic_respuesta) + "\n"
    try:
        print(f"El resultado es: {respuesta}")
        socket_server.sendall(respuesta.encode("utf-8"))
    except OSError as e:
        print(f"Ocurrió un error: {e}")




send_presentation()
print(f"Conectado a un nodo en: {HOST1}:{PORT1}")
try:
    recibir()
except KeyboardInterrupt:
    print("Célula servidor cerrada por el usuario")
    socket_server.close()