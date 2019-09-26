#Our proxy implementation
import sys, socket, thread

BUFFER_SIZE = 8192 #maximum buffer size for socket

#List of forbidden expressions
FORBIDDEN = ["SpongeBob", "Britney Spears", "Paris Hilton", "Norrk??ping"]

#Parses the url into webserver and port
def parse(url):
    http_pos = url.find("://")
    if (http_pos==-1):
        temp = url
    else:
        temp = url[(http_pos+3):]

    #find the port position if any
    port_pos = temp.find(":")

    # find end of web server
    webserver_pos = temp.find("/")
    if webserver_pos == -1:
        webserver_pos = len(temp)

    webserver = ""
    port = -1
    if (port_pos==-1 or webserver_pos < port_pos): #default port
        port = 80
        webserver = temp[:webserver_pos]
    else: # specific port
        port = int((temp[(port_pos+1):])[:webserver_pos-port_pos-1])
        webserver = temp[:port_pos]
    
    return (webserver, port)

#prints info about request
def printout(type,request):
    print type.upper(), "\t", request

#needed to redirect the client to NetNinny if forbidden website is requested
def redirect(url):
    webserver, _ = parse(url)
    printout("Redirected to", url)
    return "HTTP/1.1 302 Found\r\nLocation: " + url + "\r\nHost: " + webserver + "\r\nConnection: close\r\n\r\n"

#called from process_request function
def proxy_server(conn, client_addr, request, url, isForbiddenUrl, needContentCheck):
    try:
        # parse the url to get webserver and port info
        webserver, port = parse(url)
        # create a socket to connect to the web server
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((webserver, port))

        if isForbiddenUrl:
            #redirect client to error page
            conn.send(redirect("http://zebroid.ida.liu.se/error1.html"))
            #needed to avoid Broken Pipe problem
            s.shutdown(socket.SHUT_RDWR)
            conn.shutdown(socket.SHUT_RD)
        else:
            s.send(request) # send request to webserver
            while True:
                # receive data from web server
                reply = s.recv(BUFFER_SIZE)
                if (len(reply) > 0):
                    #check for forbidden words in the message body
                    isBadContent = False
                    if needContentCheck: #not media file type
                        lines = reply.split("\n")
                        for line in lines:
                            for expression in FORBIDDEN:
                                if " " in expression:
                                    if all(word in line for word in expression.split(' ')):
                                        isBadContent = True
                                        break
                                if expression in line:
                                    isBadContent = True
                                    break
                            if isBadContent:
                                printout("Forbidden Content", url)
                                break 

                    if isBadContent:
                        #redirect client to error page
                        conn.send(redirect("http://zebroid.ida.liu.se/error2.html"))
                        #needed to avoid Broken Pipe problem
                        s.shutdown(socket.SHUT_RDWR)
                        conn.shutdown(socket.SHUT_RD)
                    else:
                        # not forbidden, send the reply to client
                        conn.send(reply)
                else: #stop the connection if failed to receive data
                    break
        s.close() #after done, close the server socket
        conn.close() #close the client socket
    except socket.error, (value, message):
        s.close()
        conn.close()
        print ("Runtime Error:", message)
        sys.exit(1)

#called to process the request from client
def process_request(conn, client_addr):
    try:    
        # get the request from browser
        request = conn.recv(BUFFER_SIZE)
        # parse the first line
        first_line = request.split('\n')[0]
        # get url
        url = first_line.split(' ')[1]
        
        printout("Request",first_line)

        #check for forbidden word in url
        isForbiddenUrl = False
        for expression in FORBIDDEN:
            if " " in expression:
                if all(word in url for word in expression.split(' ')):
                    isForbiddenUrl = True
                    break
            if expression in url:
                isForbiddenUrl = True
                break
        if isForbiddenUrl:
            printout("Forbidden URL", url)
        
        #do we need to check the content?
        needContentCheck = True
        #do not check the content for following file types
        notChecked = [".jpg", ".jpeg", ".gif", ".png", ".js", ".cs"]
        for x in notChecked:
            if url.endswith(x):
                needContentCheck = False
                break

        #in this function the request is handled furhter
        proxy_server(conn, client_addr, request, url, isForbiddenUrl, needContentCheck)
    except Exception, e:
        pass


#The program starts running from here

#Ask for listnening port from user
try:
    listening_port = int(raw_input("Enter listeting port number: "))
except KeyboardInterrupt: #if ctrl-c is pressed
    print("\n")
    print("Ctrl-C pressed. Application is shutting down")
    sys.exit()

#initialize the socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #reuse the socket port
    s.bind(('', listening_port))
    s.listen(10)
    print("Socket initialized")
except Exception, e:
    print("Cannot initialize socket")
    sys.exit(2)

while True:
    try:
        #accept connection from client
        conn, client_addr = s.accept()
        # create a thread to handle request
        thread.start_new_thread(process_request, (conn, client_addr))
    except KeyboardInterrupt:
        s.close()
        print("\n Proxy shut down")
        sys.exit(1)
s.close()