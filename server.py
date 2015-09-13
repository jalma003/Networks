import socket
import sys
import thread
 
HOST = '10.0.0.4'   # Symbolic name meaning all available interfaces
PORT = 7120 # Arbitrary non-privileged port
 
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print 'Socket created'

# Username, password, id. ID is used used in the subscription list
accounts = []
accounts.append(("jalma003", "pass", 0))
accounts.append(("mtobo002", "hello", 1))
accounts.append(("avene003", "yes", 2))

subscription_list = []
subscription_list.append([])
subscription_list.append([])
subscription_list.append([])
subscription_list[0].append("mtobo002")
subscription_list[0].append("water")
subscription_list[2].append("mtobo002")

offline_messages_list = []
offline_messages_list.append(("jalma003", "avene003", "Hello test"))
offline_messages_list.append(("jalma003", "mtobo002", "Hello there1"))
offline_messages_list.append(("jalma003", "mtobo002", "Hello there2"))
offline_messages_list.append(("jalma003", "mtobo002", "Hello there3"))
offline_messages_list.append(("jalma003", "mtobo002", "Hello there4"))
offline_messages_list.append(("jalma003", "mtobo002", "Hello there5"))
offline_messages_list.append(("jalma003", "mtobo002", "Hello there6"))
offline_messages_list.append(("jalma003", "mtobo002", "Hello there7"))


conn_list = []

all_message_list = []

hash_list = []
hash_list.append(("jalma003", "python", "This language is easy #python"))
hash_list.append(("avene003", "python", "Hello there #python"))

#Bind socket to local host and port
try:
    s.bind((HOST, PORT))
except socket.error , msg:
    print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
    sys.exit()
     
print 'Socket bind complete'
 
#Start listening on socket
s.listen(10)
print 'Socket now listening'


def get_uid(uname):
    for user in accounts:
        if user[0] == uname:
            return user[2]
    return -1

def edit_subs(conn, uname):
    global subscription_list
    uid = get_uid(uname)
    while(1):
        msg = conn.recv(1024)
        if msg == "q":
            return
        option, friend = msg.split("|")
        if option == "1":
            if get_uid(friend) >= 0:
                if friend in subscription_list[uid]:
                    conn.send("edit_subs|Invalid|Already subscribed!")
                    continue
                else:
                    subscription_list[uid].append(friend)
                    conn.send("edit_subs|valid|You are now subscribed to " + friend)
                    return
            else:
                conn.send("edit_subs|Invalid|" + friend + " is not a valid username")
        elif option == "2":
            subs_list = ""
            for user in subscription_list[uid]:
                subs_list = subs_list + user + "\n"
            conn.send("edit_subs|" + subs_list)
            drop = conn.recv(1024)
            if drop not in subscription_list[uid]:
                conn.send("edit_subs|Invalid")
                continue
            else:
                subscription_list[uid].remove(drop)
                conn.send("edit_subs|valid")
                return
        elif option == "3":
            print friend
            subscription_list[uid].append(friend)
            return

def search(conn):
    word = conn.recv(1024)
    if word == "q":
        return
    found_flag = False
    for i in hash_list:
        if i[1] == word:
            found_flag = True
            conn.send("search|" + i[0] + "|" + i[2])
            conn.recv(1024)
    if found_flag == False:
        conn.send("search|invalid")
        conn.recv(1024)
    else:
        conn.send("search|done")
        conn.recv(1024)
    
def post_message(conn, uname):
    global offline_messages_list
    global conn_list
    global all_message_list
    global hash_list

    msg = conn.recv(1024)
    if msg == 'q':
        return
    received_flag = False
    word = ""
    message, hash_tag = msg.split("|")
    count = 0
    for i in hash_tag:
        if i == "#":
            temp = hash_tag[count:]
            if temp.find(" ") != -1:
                word = temp[1: temp.find(" ")]
            else:
                word = temp[1:]
            hash_list.append((uname, word, message))
            for user in accounts:
                for sub in subscription_list[user[2]]:
                    if word == sub:
                        for connection in conn_list:
                            if user[0] == connection[0]:
                                connection[1].send("post|" + "from #" + word + " by " + uname + "|" + message)
        count += 1


    all_message_list.append(uname + "|" + message)

    for user in accounts:
        received_flag = False
        if user[0] == uname:
            continue
        elif uname in subscription_list[user[2]]:
            for connection in conn_list:
                if user[0] == connection[0]:
                    received_flag = True
                    connection[1].send("post|" + uname + "|" + message)
            if received_flag == False:
                offline_messages_list.append((user[0], uname, message))

def send_offline_msg(conn, uname):
    global offline_messages_list
    remove_list = []
    count = 0
    for msg in reversed(offline_messages_list):
        if msg[0] == uname:
            count += 1
            conn.send("offline_msg|" + msg[1] + "|" + msg[2])
            conn.recv(1024)
            remove_list.append(msg)
            if count == 10:
                break

    for msg in remove_list:
        offline_messages_list.remove(msg)

def logout(conn, uname):
    global conn_list
    conn_list.remove((uname, conn))
    print uname + " has signed out"
    thread.exit()

def see_followers(conn, uname):
    index = 0
    for sub in subscription_list:
        if uname in sub:
            for account in accounts:
                if index == account[2]:
                    conn.send("see_followers|" + account[0])
                    conn.recv(1024)
        index += 1
    conn.send("see_followers|done")
    return

def run(conn, uname):
    send_offline_msg(conn, uname)
    while(1):
        option = conn.recv(1024)
        if option == "2":
            edit_subs(conn, uname)
        elif option == "3":
            post_message(conn, uname)
        elif option == "4":
            logout(conn, uname)
        elif option == "5":
            search(conn)
        elif option == "6":
            see_followers(conn, uname)
        else:
            conn.send("Invalid")

def signin(conn):
    global conn_list
    while 1:
        user_info = conn.recv(1024)
        uname, password = user_info.split("|")
        for user in accounts:
            if user[0] == uname and user[1] == password:
                conn.send("signin|valid")
                conn.recv(1024)
                conn_list.append((uname, conn))
                print uname + " has signed in"
                return run(conn, uname)
        conn.send("signin|Invalid")

def admin():
    global subscription_list
    global accounts
    while(1):
        option = raw_input("")
        if option == "messagecount":
            print len(all_message_list)
        elif option == "usercount":
            print len(conn_list)
        elif option == "storedcount":
            print len(offline_messages_list)
        elif option == "newuser":
            uname = raw_input("Username: ")
            password = raw_input("Password: ")
            accounts.append((uname, password, accounts[len(accounts)-1][2] + 1))
            subscription_list.append([])

thread.start_new_thread(admin, ())

while 1:
    conn, addr = s.accept()
    print "Connected with " + str(addr[0]) + ": " + str(addr[1])
    thread.start_new_thread(signin, (conn,))

s.close()