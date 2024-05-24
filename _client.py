import socket
import threading
import logging
import tkinter as tk
import json
from tkinter import scrolledtext

logging.basicConfig(level=logging.DEBUG, format='%(threadName)s %(message)s')
logger = logging.getLogger()

with open("clientsettings.json") as file:
    c = json.load(file)
    a,b = c["address"],c["port"]


server_address = (a, b)  # IP, port

class Receiver(threading.Thread):
    def __init__(self, event, text_widget):
        super().__init__()
        self.stop = event
        self.text_widget = text_widget
        
    def run(self):
        while not self.stop.is_set():
            try:
                msg = sock.recv(1024).decode()
                if msg == "BYE":
                    self.update_text("\nack received.")
                    try:
                        root.destroy()
                    except:
                        pass
                    quit()
                    return
                self.update_text(f"{msg}")
            except Exception as e:
                self.update_text(f"Exception in receiver thread: {e}")
    
    def update_text(self, message):
        self.text_widget.configure(state='normal')
        self.text_widget.insert(tk.END, message + "\n")
        self.text_widget.configure(state='disabled')
        self.text_widget.see(tk.END)

def send_message(event=None):
    msg = input_entry.get()
    if msg:

        if msg == "/clear":
            text_area.configure(state='normal')
            text_area.delete(1.0, tk.END)
            text_area.configure(state='disabled')
        else:        
            sock.sendall(msg.encode())
        input_entry.delete(0, tk.END)
        if msg == ">DISCONNECT<":
            stopevent.set()
            sock.send(">DISCONNECT<".encode())
            text_area.insert(tk.END, "disconnect message sent, awaiting for acknowledge...\n")
            input_entry.configure(state='disabled')

# Initialize socket connection
print("attempting connection...")
sock = socket.socket()
sock.connect(server_address)
print("connection successful!")

# Initialize Tkinter window
root = tk.Tk()
root.title("Chat Client")

text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, state='disabled', height=20)
text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

input_entry = tk.Entry(root)
input_entry.pack(padx=10, pady=10, fill=tk.X)
input_entry.bind("<Return>", send_message)

stopevent = threading.Event()
rec = Receiver(stopevent, text_area)
rec.start()

try:
    root.mainloop()
except KeyboardInterrupt:
    pass

try:
    root.destroy()
except:
    pass
stopevent.set()

try:
    sock.send(f"/chat leave".encode())
except:
    pass

sock.send(">DISCONNECT<".encode())
##print("disconnect message sent, awaiting for acknowledge...")
##
##rec.join()
##sock.close()

print("execution terminated.")
quit()
