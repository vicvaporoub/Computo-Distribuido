import socket as s
import tkinter as tk
import os
import re
import time
from threading import Thread, Lock
import json
import uuid
import sys
HOST1 = 'localhost'
if len(sys.argv) < 2:
    print("Necesita ingresar un numero de puerto")
    sys.exit()
PORT1 = int(sys.argv[1])

RUTA_ARCHIVO = f"gui_{os.getpid()}_PORT{PORT1}.txt"
file_lock = Lock()
id_unico = str(uuid.uuid4())
pendientes = {}
c_c = { 
    "+" : "SUM_REQ",
    "-" : "SUB_REQ", 
    "*": "MUL_REQ", 
    "/" : "DIV_REQ" 
    }


def button_click(value):
    current = entry.get()
    entry.delete(0, tk.END)
    entry.insert(tk.END, current + str(value))

def clear_entry():
    entry.delete(0, tk.END)

def backspace():
    current = entry.get()
    entry.delete(0, tk.END)
    entry.insert(tk.END, current[:-1])

def openFile(expression, result):
    with file_lock:
        with open(RUTA_ARCHIVO, "a", encoding="utf-8") as file:
            file.write(f"Expresión: {expression} = {result} \n")
def send_presentation():
    tipo = "GUI"
    dic = json.dumps({"tipo": tipo, "id": id_unico}) + "\n"
    print(dic)
    try:
        socket_client.sendall(dic.encode("utf-8"))
    except Exception as e:
        print(f"Ocurrió un error: {e}")
def send_expression():

    expression = entry.get()
    operandos = re.findall(r'\d+', expression)
    operandos = list(map(int, operandos))

    operador = re.findall(r'[+\-*/]', expression)
    operador = "".join(map(str, operador))

    if len(operandos) != 2:
        entry.insert(tk.END, "ERROR")
        return
    if len(operador) != 1:
        entry.insert(tk.END, "ERROR")
        return
    id_numerico = str(uuid.uuid4())
    codigo = c_c[operador]
    pendientes[id_numerico] = expression


    dic = json.dumps({'codigo_de_contenido': codigo, 'operandos': operandos, 'ID_celula_og': id_unico, 'ID_mensaje': id_numerico}) + "\n"
    print(dic)
    try:
        socket_client.sendall(dic.encode("utf-8"))
    except Exception as e:
        print(f"Ocurrió un error: {e}")


root = tk.Tk()
root.title(f"GUI: PORT {PORT1}")
root.geometry("400x500")
root.config(bg="#282c35")  

entry = tk.Entry(root, width=20, font=('Arial', 20), justify=tk.RIGHT, bd=10)
entry.grid(row=0, column=0, columnspan=4, padx=10, pady=10, ipady=20)  

# Buttons
buttons = [
    '7', '8', '9', '/',
    '4', '5', '6', '*',
    '1', '2', '3', '-',
    '0', '=', '+'
]

row_val = 1
col_val = 0

for button in buttons:
    tk.Button(
        root, text=button, padx=20, pady=20, font=('Arial', 16),
        command=lambda b=button: button_click(b) if b != '=' else send_expression(),    
        bg="#61dafb", 
        fg="#282c35"   
    ).grid(row=row_val, column=col_val, sticky="nsew")  
    col_val += 1
    if col_val > 3:
        col_val = 0
        row_val += 1

tk.Button(
    root, text='C', padx=20, pady=20, font=('Arial', 16),
    command=clear_entry, bg="#ff6b6b", fg="#282c35"
).grid(row=row_val, column=col_val, sticky="nsew")
col_val += 1
tk.Button(
    root, text='⌫', padx=20, pady=20, font=('Arial', 16),
    command=backspace, bg="#ff6b6b", fg="#282c35"
).grid(row=row_val, column=col_val, sticky="nsew")

for i in range(1, 5):
    root.grid_rowconfigure(i, weight=1)
    root.grid_columnconfigure(i, weight=1)

def receive():

    lector = socket_client.makefile("r", encoding="utf-8")
    
    while True:
        try:
            linea = lector.readline()
        except OSError:
            linea = ""
        if not linea:
            print("El nodo cerró la conexión")
            socket_client.close()
            root.after(0, root.destroy)
            break
        dic = json.loads(linea)
        if dic["codigo_de_contenido"].endswith("_RES"):
            if dic["ID_solicitud_original"] not in pendientes:
                continue
            expresion = pendientes[dic["ID_solicitud_original"]]
            root.after(0, actualizar_entry, dic["resultado"], expresion)#le pide al hilo principal interactuar con la ventana de tk
        # y no es seguro cambiar algún aspecto de la interfaz de usuario desde un hilo secundario(rvs)
             

def actualizar_entry(result, expression):
    entry.delete(0, tk.END)
    entry.insert(tk.END, result)
    openFile(expression, result)

# Main loop
socket_client = s.socket(s.AF_INET, s.SOCK_STREAM)
socket_client.connect((HOST1, PORT1))

send_presentation()
print(f"Conectado a un nodo en: {HOST1}:{PORT1}")
Thread(target=receive, daemon=True).start()

root.mainloop()
socket_client.close()
