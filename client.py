import socket
import sys
import select
import thread
import getpass
 
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except socket.error:
    print 'Failed to create socket'
    sys.exit()
 
host = '169.235.29.115';
port = 7120;

s.connect((host, port))
received_msg = []
offline_msg_list = []

def retrieve_msg(option):
    global received_msg
    while(1):
        for msg in received_msg:
            if option in msg:
                received_msg.remove(msg)
                return msg.replace(option + "|", "")

def signin():
    print "Welcome! Please sign in. Press 'q' to quit"
    while(1):
        uname = raw_input("Username: ")
        if uname == "q":
            return False
        password = getpass.getpass()
        if password == "q":
            return False        
        s.send(uname + "|" + password)
        msg = retrieve_msg("signin")
        if msg == "valid":
            print "You are now signed in as " + uname + "\n"
            s.send("ACK")
            return True
        else:
            print "Invalid username of password. Please try again"

def edit_subs():
    while(1):
        option = raw_input("1. Subscribe to new user\n2. Drop User\n3. Subscribe to hashtag\n(press \'q\' at anytime to return to the main menu)\n")
        if option == "q":
            s.send("q")
            return
        if option == "1":
            user = raw_input("Username: ")
            if user == "q":
                s.send("q")
                return
            s.send(option + "|" + user)
            msg = retrieve_msg("edit_subs")
            print msg
            status, reply = msg.split("|")
            if status == "Invalid":
                print reply + " Try again."
                continue
            else:
                print reply
                return
        elif option == "2":
            s.send(option + "|list request")
            subs_list = retrieve_msg("edit_subs")
            print subs_list
            user = raw_input("Which subscription would you like to drop? (press \'q\' at anytime to go back to the main menu)\n")
            if user == "q":
                s.send("q")
                return
            s.send(user)
            status = retrieve_msg("edit_subs")
            if status == "Invalid":
                print "Invalid entry. Try again"
                continue
            else:
                print "Subscription dropped"
                return
        elif option == "3":
            hashtag = raw_input("What hashtag would you like to subscribe too? (press \'q\' at anytime to go back to the main menu)\n")
            s.send(option + "|" + hashtag)
            print "You have been subscribed to hashtag " + hashtag
        else:
            print "This is an invalid option. Please try again."

def post_msg():
    while(1):
        message = raw_input("Message (press \'q\' at anytime to return to the main menu): ")
        if message == "q":
            s.send("message")
            return
        if len(message) > 140:
            print "Your message is too long. Please try again"
        else:
            hash_tag = raw_input("Enter the a hash tags: ")
            hash_list = hash_tag.split(" ")
            hash_tag = ""
            for tag in hash_list:
                hash_tag = hash_tag + "#" + tag + " "
            message = message + "|" + hash_tag
            s.send(message)
            print "Your message has been posted!"
            return

def hashtag_search():
    word = raw_input("What would you like to search? (press \'q\' at anytime to return to the main menu)\n")
    if word == "q":
        s.send(word)
        return
    s.send(word)
    while(1):
        msg = retrieve_msg("search")
        if msg == "done":
            return
        elif msg == "invalid":
            print "There are no results matching \'" + word + "\'."
            return
        else:
            by, content = msg.split("|")
            print by + ": " + content

def get_offline_messages():
    global offline_msg_list
    while(1):
        option = raw_input("1. View all messages\n2. View messages from subscription\n(press \'q\' at anytime to go back to the main menu)\n")
        if option != "1" and option != "2":
            print("Not a valid option. Try again.")
        elif option == "1":
            for msg in offline_msg_list:
                print "By " + msg[0] + ":\n\t" + msg[1]
            del offline_msg_list[:]
            return
        else:
            sentby_list = []
            for user in offline_msg_list:
                if user[0] not in sentby_list:
                    print user[0]
                    sentby_list.append(user[0])
            users = raw_input("From who would you like to view messages? (press \'q\' at anytime to go back to the main menu)\n")
            user_list = users.split(" ")
            offline_read_list = []
            for user in offline_msg_list:
                if user[0] in user_list:
                    print "By " + user[0] + ": " + user[1] + "\n"
                    offline_read_list.append(user)
            for msg in offline_read_list:
                offline_msg_list.remove(msg)
            return

def see_followers():
    print "People following you: "
    while(1):
        follower = retrieve_msg("see_followers")
        if follower == "done":
            return
        else:
            print follower

def menu():
    print "--------Welcome--------\n"
    if len(offline_msg_list) > 0:
            print "You have " + str(len(offline_msg_list)) + " unread post!!!"
    while(1):
        print "--------- Menu ---------"
        print "1: See offline messages (" + str(len(offline_msg_list)) + ")"
        print "2: Edit Subscription"
        print "3: Post a Message"
        print "4: Logout"
        print "5: Hashtag Search"
        print "6. See followers"
        option = raw_input("")
        if option != "1":
            s.send(option)

        if option == "1":
            get_offline_messages()
        elif option == "2":
            edit_subs()
        elif option == "3":
            post_msg()
        elif option == "4":
            return -1
        elif option == "5":
            hashtag_search()
        elif option == "6":
            see_followers()
        else:
            print "That was not a valid entry. Please try again"

def incoming_msg():
    global received_msg
    global offline_msg_list
    while(1):
        message = s.recv(1024)
        if "post" in message:
            msg_type, from_user, msg = message.split("|")
            s.send("ACK")
            print "New post from " + from_user + ": \n" + msg
        elif "offline_msg" in message:
            msg_type, from_user, msg = message.split("|")
            s.send("ACK")
            offline_msg_list.append((from_user, msg))
        elif message not in received_msg:
            received_msg.append(message)
            if "signin" not in message and "edit_subs" not in message:
                s.send("ACK")

thread.start_new_thread(incoming_msg, ())
while(1):
    if signin():
        if menu() < 0:
            print "Goodbye"
            break;
