import socket as s
import os
middleware_host = "127.0.0.1"
port=50002
RUTA_ARCHIVO = f"results.txt"

def openFile(expression, result):
    with open(RUTA_ARCHIVO, "a", encoding="utf-8") as file:
        file.write(f"Expresión: {expression} = {result} \n")

def calculate(expression):
    """Evaluate a simple arithmetic expression"""
    try:
        if not all(c in "0123456789+-*/. " for c in expression):
            return "Error: Invalid characters in expression."

        result = eval(expression)
        openFile(expression, result)
        return str(result)
    except Exception as e:
        return f"Error: {e}"
    
def server_program():
    """Start a simple calculator servers"""

    with s.socket(s.AF_INET, s.SOCK_STREAM) as socket:
        try:
            socket.connect((middleware_host, port))
            print(f"Connected to middleware at {middleware_host}:{port}")
            
            while True: 
                data = socket.recv(1024)
                try:
                    if not data:
                        print("Middleware cerró la conexión.")
                        break
                    expression = data.decode("utf-8")
                    result = calculate(expression)

                    mensaje = f"{expression}|{result}"
                    socket.sendall(mensaje.encode("utf-8"))
                    
                    print(f"Procesado: {expression} = {result}")
                except Exception as e:
                    return f"Error: {e}"

        except ConnectionRefusedError:
            print(
                f"Could not connect to middleware at {middleware_host}:{port}. Is the middleware running?"
            )
        except Exception as e:
            print(f"An error occurred: {e}")

server_program()