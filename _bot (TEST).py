print("importing libraires...")
import requests,time,json,socket
import ollama,torch

USERNAME = "B00001"
PASSWORD = "passwo"
ACTIVATOR = "!"

CHAT = "lobby"

##print(torch.cuda.FloatTensor())
##device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class Responsator:
    def __init__(self):
        self.messages = []
        self.addmessage("you are a helpful bot inserted in a chat, and you have been created to answer questions from the user.","system")



    def answer(self,topic):
        print(topic)
        self.addmessage(topic)

##        r = ollama.chat(model="gemma",messages=self.messages) 
        r = ollama.chat(model="gemma:2b",messages=self.messages)  # stupid, but really fast
##        r = ollama.chat(model="llama3",messages=self.messages)    # slow as fuck

        
        self.addmessage(r["message"]["content"],role="assistant")
        return r["message"]["content"]


    def addmessage(self,content,role="user"):
        p = {
            "role":role,
            "content":content
            }
        self.messages.append(p)
        print(self.messages)


with open("clientsettings.json") as file:
    c = json.load(file)
    a,b = c["address"],c["port"]


server_address = (a, b)  # IP, port


# Initialize socket connection
print("attempting connection...")
sock = socket.socket()
sock.connect(server_address)
print("connection successful!")


sock.sendall(f"/login {USERNAME} {PASSWORD}".encode())
print(sock.recv(1024).decode())
time.sleep(0.2)
sock.sendall(f"/chat join {CHAT}".encode())
print(sock.recv(1024).decode())
time.sleep(0.2)



rur = Responsator()
print("joinamento completussato.")
while True:
    msg = sock.recv(1024).decode()
    print("msgrcvd!")
    if not msg.startswith("<"):
        continue
    msg = msg.split(">")[1].strip()
    if not msg.startswith(ACTIVATOR):
        continue

    msg = msg[1:]
    if msg.strip() == "purge":
        sock.sendall("purging memory...".encode())
        rur = Responsator()
        sock.sendall("memory purged!".encode())
    else:
        print(msg)
        print("preparing response...")
        sock.sendall(f"{rur.answer(msg)}".encode())
        print("response sent!")
    

















