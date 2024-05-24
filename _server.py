from socketserver import TCPServer, BaseRequestHandler, ThreadingMixIn
import json,time,threading

PORT = 2003



def updateUserList():
    with open("userinfo.json","w") as file:
        json.dump(userinfo,file,indent=6)
        

def syncMessages():
    while True:
        with open("chatinfo.json","w") as file:
            json.dump(chatinfo,file,indent=6)
        time.sleep(5)


def sendToAll(users,chat,message):
    for user in users:
        if user.selectedChat == chat:
            user.request.sendall(f"{message}".encode())



try:
    with open("userinfo.json") as file:
        userinfo = json.load(file)
except OSError:
    userinfo = {}


try:
    with open("chatinfo.json") as file:
        chatinfo = json.load(file)
except OSError:
    chatinfo = {}




    


syncthread = threading.Thread(target=syncMessages,daemon=True)
syncthread.start()

ThreadingMixIn.daemon=True
class DefaultServer(ThreadingMixIn,TCPServer):
    allow_reuse_address = True

class DefaultRequestHandler(BaseRequestHandler):

    connectedClients = []   

    def handle(self):
        global userinfo,chatinfo

        
        self.client_ip = self.client_address[0]
        self.client_port = self.client_address[1]
        print(f"Client connected from {self.client_ip}:{self.client_port}")
        self.loggedIn = False
        self.selectedChat = None
        self.username = "anon"
        self.__class__.connectedClients.append(self)


        while True:
            data = self.getMessage()

            if data == ">DISCONNECT<":
                self.request.send("BYE".encode())
                break

            
            print(f"new message received:\n{data}\n")

# - - - - - - - - - - - - - - COMAND HANDLING - - - - - - - - - - - - - - - - - - #

            if data.startswith("/"):
                data = data[1:]

                raw = data.split(" ")


                if raw[0] == "help" and len(raw) == 1:
                    out = "available commands:\n"
                    out += "/help ------------------------------ Show this menu.\n"
                    out += "/login {username} {password} ------- Log into your account.\n"
                    out += "/register {username} {password} ---- Register a new account.\n"
                    out += "/loginstatus ----------------------- Check your login status.\n"
                    out += "/logout ---------------------------- Log out from your account.\n"
                    out += "/quit ------------------------------ Disconnect from the server.\n"
                    out += "/kick {username} ------------------- Disconnect another user from the server (owner only).\n"
                    out += "/kick @a --------------------------- Disconnect every user from the server (owner only).\n"  
                    out += "/chat create {chatname} ------------ Create a new chat.\n"
                    out += "/chat select {chatname} ------------ Join an existing chat.\n"
                    out += "/chat join {chatname} -------------- Alias for /chat select.\n"
                    out += "/chat delete {chatname} ------------ Delete an existing chat (owner only).\n"
                    out += "/chat remove {chatname} ------------ Alias for /chat delete.\n"
                    out += "/chat sync ------------------------- Get every message in history.\n"
                    out += "/chat leave ------------------------ Leave the current chat.\n"
                    out += "/chat quit ------------------------- Alias for /chat leave.\n"
                    out += "/chat list ------------------------- List all available chats.\n"
                    out += "/chat purge ------------------------ Purge the message history of the current chat (owner only).\n"
                    out += "/clear ----------------------------- Clear the console (client side).\n"
                    out += "/whitelist enable ------------------- Enable whitelist for the current chat (owner only).\n"
                    out += "/whitelist disable ------------------ Disable whitelist for the current chat (owner only).\n"
                    out += "/whitelist add {username} ----------- Add user to whitelist (owner only).\n"
                    out += "/whitelist remove {username} -------- Remove user from whitelist (owner only).\n"
                    self.request.send(out.encode())


                elif raw[0] == "login" and len(raw) == 3:
                    usn = raw[1]
                    pw = raw[2]

                    if usn not in userinfo.keys():
                        self.request.send("ER/01/This username does not exist.".encode())
                        continue
                    elif pw != userinfo[usn]:
                        self.request.send("ER/02/Wrong password.".encode())
                        continue
                    elif self.loggedIn:
                        self.request.send("ER/04/You're already logged in!".encode())
                        continue                        
                    else:
                        self.loggedIn = True
                        self.username = usn
                        self.request.send("SC/00/You are now logged in.".encode())

                        
                elif raw[0] == "register" and len(raw) == 3:
                    usn = raw[1]
                    pw = raw[2]

                    if usn in userinfo.keys():
                        self.request.send("ER/03/This username already exists.".encode())
                        continue
                    elif self.loggedIn:
                        self.request.send("ER/05/You're already logged in!".encode())
                        continue 
                    else:
                        userinfo[usn] = pw
                        updateUserList()
                        self.loggedIn = True
                        self.username = usn
                        self.request.send("SC/01/Registration successful, you are now logged in.".encode())


                elif raw[0] == "quit":
                    if self.selectedChat is not None:
                        sendToAll(self.__class__.connectedClients,self.selectedChat,f"{self.username} left the chat.")
                    self.request.send("BYE".encode())
                    return


                elif raw[0] == "loginstatus":
                    if self.loggedIn:
                        self.request.send(f"You're currently logged in as {self.username}.".encode())
                    else:
                        self.request.send(f"You're currently not logged in.".encode())


                elif raw[0] == "logout":
                    if self.loggedIn:
                        self.loggedIn = False
                        self.username = None
                        self.request.send("SC/02/Logout successful.".encode())
                    else:
                        self.request.send("ER/06/No profile found, nothing changed.".encode())
                        continue


                elif raw[0] == "chat" and len(raw) == 3:
                    if raw[1] == "create":
                        newname = raw[2]

                        if not self.loggedIn:
                            self.request.send("ER/07/You can't create a chat while not logged in.".encode())
                            continue                            
                        elif newname in chatinfo.keys():
                            self.request.send("ER/08/Chat name already exists.".encode())
                            continue
                        else:
                            chatinfo[newname] = {"owner":self.username,"messages":[],"whitelist_enabled":False,"whitelist":[self.username]}
                            self.request.send("SC/03/chat creation successful.".encode())
                            self.selectedChat = newname

                    elif raw[1] in ["select","join"]:
                        name = raw[2]

                        if name not in chatinfo.keys():
                            self.request.send("ER/09/Chat does not exist.".encode())
                            continue
                        elif not self.loggedIn:
                            self.request.send("ER/10/You can't join a chat while not logged in.".encode())
                            continue
                        elif self.selectedChat is not None:
                            self.request.send("ER/17/You can't join a chat while you are already in one.".encode())
                            continue
                        elif chatinfo[name]["whitelist_enabled"] and self.username not in chatinfo[name]["whitelist"]:
                            self.request.send("ER/25/You are not whitelisted in this chat!".encode())
                            continue                            
                        
                        else:
                            self.request.send(f"SC/04/Chat joined successfully. Welcome to {name}!".encode())
                            sendToAll(self.__class__.connectedClients,name,f"{self.username} joined the chat.")
                            
                            self.selectedChat = name

                    elif raw[1] in ["delete","remove"]:
                        name = raw[2]
                        if name not in chatinfo.keys():
                            self.request.send("ER/012/Chat does not exist.".encode())
                            continue
                        elif not self.loggedIn:
                            self.request.send("ER/13/You can't delete a chat while not logged in.".encode())
                            continue                        
                        elif self.username != chatinfo[name]["owner"]:
                            self.request.send("ER/14/Only the owner of the chat can delete it.".encode())
                            continue
                        elif self.selectedChat == name:
                            self.request.send("ER/16/You can't delete the chat you are currently connected to.".encode())
                            continue
                        else:
                            
                            for user in self.__class__.connectedClients:
                                if user.selectedChat == name:
                                    user.request.send("ER/19/The chat you were connected to has been deleted by the owner.".encode())
                                    user.selectedChat = None
                            
                            chatinfo.pop(name)
                            self.request.send(f"SC/06/Chat deleted successfully.".encode())
                            


                    else:
                        self.request.send("ER/00/Wrong syntax.".encode())
                            

                elif raw[0] == "chat" and len(raw) == 2:
                    if raw[1] in ["leave","quit"]:
                        if self.selectedChat is None:
                            self.request.send("ER/11/You haven't joined a chat yet.".encode())
                            continue                            
                        else:
                            self.request.send(f"SC/05/You left the chat.".encode())
                            temp = str(self.selectedChat)
                            self.selectedChat = None
                            sendToAll(self.__class__.connectedClients,temp,f"{self.username} left the chat.")
                            
                            

                            
                    elif raw[1] == "list":
                        if len(chatinfo.keys()) == 0:
                            self.request.send("ER/15/No chat found.".encode())
                            continue
                        else:
                            out = "Available chatrooms:\n"
                            for chat,data in chatinfo.items():
                                out += f'({data["owner"]}) - {chat} '
                                if data["whitelist_enabled"]:
                                    out += "🔒\n"
                                else:
                                    out += "\n"
                            self.request.send(out.encode())


                    elif raw[1] == "sync":
                        if self.selectedChat is None:        
                            self.request.send("ER/18/You haven't joined a chat yet.".encode())
                            continue
                        else:
                            out = "SC/07/Message history since chat creation:\n"
                            for mes in chatinfo[self.selectedChat]["messages"]:
                                out += f"\n{mes['content']}"

                            self.request.send(out.encode())


                    elif raw[1] == "purge":
                        if self.selectedChat is None:
                            self.request.send("ER/31/You can't purge messages while not connected to a chat.".encode())
                            continue
                        elif self.username != chatinfo[self.selectedChat]["owner"]:
                            self.request.send("ER/32/Only the owner of the chat can purge messages.".encode())
                            continue
                        else:
                            chatinfo[self.selectedChat]["messages"] = []
                            self.request.send("SC/013/Message history purged successfully.".encode())




                    else:
                        self.request.send("ER/00/Wrong syntax.".encode())


                elif raw[0] == "kick" and len(raw) == 2:
                    name = raw[1]

                    if self.selectedChat is None:
                        self.request.send("ER/20/You can't kick an user while not connected to a chat.".encode())
                        continue
                    elif self.username != chatinfo[self.selectedChat]["owner"]:
                        self.request.send("ER/21/Only the owner of the chat can kick an user.".encode())
                        continue
                    elif self.username == name:
                        self.request.send("ER/23/You can't kick yourself.".encode())
                        continue
                    else:
                        suc = False
                        for client in self.__class__.connectedClients:
                            if (client.username == name or (name == "@a" and client.username != self.username)) and client.selectedChat == self.selectedChat:
                                client.selectedChat = None
                                client.request.send("SC/08/You have been kicked.".encode())
                                sendToAll(self.__class__.connectedClients,self.selectedChat,f"{client.username} has been kicked.")
                                suc = True
                        if not suc:                   
                            self.request.send("ER/24/Failed to kick this user.".encode())
                            continue                            


                elif raw[0] in ["whitelist","wl"] and len(raw) == 3:
                    command = raw[1]
                    username = raw[2]

                    if self.selectedChat is None:
                        self.request.send("ER/26/You can't modify the whitelist while not connected to a chat.".encode())
                        continue                            
                    elif self.username != chatinfo[self.selectedChat]["owner"]:
                        self.request.send("ER/27/Only the owner of the chat can edit the whitelist.".encode())
                        continue

                    elif command == "add":
                        if not chatinfo[self.selectedChat]["whitelist_enabled"]:
                            self.request.send("ER/28/The whitelist is not enabled in this chat.".encode())
                            continue                              
                        elif username in chatinfo[self.selectedChat]["whitelist"]:
                            self.request.send("ER/29/This user is already whitelisted.".encode())
                            continue
                        else:
                            chatinfo[self.selectedChat]["whitelist"].append(username)
                            self.request.send("SC/09/User added to whitelist.".encode())
                            
                    elif command == "remove":
                        if not chatinfo[self.selectedChat]["whitelist_enabled"]:
                            self.request.send("ER/28/The whitelist is not enabled in this chat.".encode())
                            continue                              
                        elif username not in chatinfo[self.selectedChat]["whitelist"]:
                            self.request.send("ER/29/This user is not in the whitelist.".encode())
                            continue
                        else:
                            chatinfo[self.selectedChat]["whitelist"].pop(chatinfo[self.selectedChat]["whitelist"].index(username))
                            self.request.send("SC/010/User removed from the whitelist.".encode())                        


                    else:
                        self.request.send("ER/00/Wrong syntax.".encode())


                elif raw[0] in ["whitelist","wl"] and len(raw) == 2:
                    command = raw[1]

                    if self.selectedChat is None:
                        self.request.send("ER/26/You can't modify the whitelist while not connected to a chat.".encode())
                        continue                            
                    elif self.username != chatinfo[self.selectedChat]["owner"]:
                        self.request.send("ER/27/Only the owner of the chat can edit the whitelist.".encode())
                        continue

                    elif command == "enable":
                        if chatinfo[self.selectedChat]["whitelist_enabled"]:
                            self.request.send("ER/30/The whitelist is already enabled in this chat.".encode())
                            continue
                        else:
                            chatinfo[self.selectedChat]["whitelist_enabled"] = True
                            self.request.send("SC/011/Whitelist enabled.".encode())    
                    elif command == "disable":
                        if not chatinfo[self.selectedChat]["whitelist_enabled"]:
                            self.request.send("ER/30/The whitelist is already disabled in this chat.".encode())
                            continue
                        else:
                            chatinfo[self.selectedChat]["whitelist_enabled"] = False
                            self.request.send("SC/012/Whitelist disabled.".encode())    
                            
                          
                else:
                    self.request.send("ER/00/Wrong syntax.".encode())


# - - - - - - - - - - - - - - MESSAGE HANDLING - - - - - - - - - - - - - - - - - - #

            elif self.selectedChat is not None:
                formatted = f"<{self.username}> {data}"                

                chatinfo[self.selectedChat]["messages"].append({
                    "user":self.username,
                    "address": f"{self.client_ip}:{self.client_port}",
                    "content":formatted
                    })

                
                for user in self.__class__.connectedClients:
                    if user.selectedChat == self.selectedChat:
                        user.request.send(formatted.encode())



            else:
                self.request.send("ER/99/You have to join a chat to send messages.".encode())

                

    def finish(self):
        print(f"the client {self.client_ip}:{self.client_port} has disconnected.")
        self.__class__.connectedClients.pop(self.__class__.connectedClients.index(self))
        self.request.close()



    def getMessage(self):
        msg = self.request.recv(1024).decode()
        return msg

server = DefaultServer(("",PORT),DefaultRequestHandler)
try:
    print(f"serving forever (port {PORT})...")
    server.serve_forever()
except KeyboardInterrupt:
    print("closing connection...")
    server.server_close()
finally:
    server.server_close()
    print("connection closed.")

