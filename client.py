import socket as s
import tkinter as tk
import os
from threading import Thread

HOST1 = 'localhost'
PORT1 = 50001
RUTA_ARCHIVO = f"clients.txt"

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
    registro_texto = f"Expresión: {expression} = {result} \n"
    try:
        with open(RUTA_ARCHIVO, "r", encoding="utf-8") as file:
            contenido = file.readlines()
            if registro_texto in contenido:
                return  # Si la línea ya existe, salimos de la función sin escribir
    except FileNotFoundError: 
        #Como es la primera vez que haces un cálculo, el archivo no existe. Python lanza el error FileNotFoundError
        pass #pero usamos pass para que no salte el error y con el siguiente with open se cree el archivo

    # Al usar el modo "a", Python se da cuenta de que el archivo no existe, lo crea en ese mismo instante
    # 2. Si el registro no existía en el archivo, procedemos a escribirlo
    with open(RUTA_ARCHIVO, "a", encoding="utf-8") as file:
        file.write(registro_texto)

def send_expression(host="localhost", port=50001):
    expression = entry.get()

    try:
        socket_client.sendall(expression.encode("utf-8"))
    except Exception as e:
        print(f"Ocurrió un error: {e}")


root = tk.Tk()
root.title("Colorful Calculator")
root.geometry("400x500")
root.config(bg="#282c35")  

entry = tk.Entry(root, width=20, font=('Arial', 20), justify=tk.RIGHT, bd=10)
entry.grid(row=0, column=0, columnspan=4, padx=10, pady=10, ipady=20)  

# Buttons
buttons = [
    '7', '8', '9', '/',
    '4', '5', '6', '*',
    '1', '2', '3', '-',
    '0', '.', '=', '+'
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
    
    while True:
        data = socket_client.recv(1024)
        mensaje_recibido = data.decode("utf-8")
        if "|" in mensaje_recibido:
                expression, result = mensaje_recibido.split("|", 1)
        root.after(0, actualizar_entry, result, expression)#le pide al hilo principal interactuar con la ventana de tk
        # y no es seguro cambiar algún aspecto de la interfaz de usuario desde un hilo secundario(rvs)

def actualizar_entry(result, expression):
    entry.delete(0, tk.END)
    entry.insert(tk.END, result)
    openFile(expression, result)

# Main loop
socket_client = s.socket(s.AF_INET, s.SOCK_STREAM)
socket_client.connect((HOST1, PORT1))
print(f"Conectado al middleware en: {HOST1}:{PORT1}")
Thread(target=receive).start()

root.mainloop()
