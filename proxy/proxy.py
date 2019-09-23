#Our proxy implementation
import sys, socket, thread

BUFFER_SIZE = 8192

def proxy_server(conn, client_addr, request, webserver, port):
    try:
        # create a socket to connect to the web server
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((webserver, port))
        s.send(request)         # send request to webserver

        while True:
            # receive data from web server
            reply = s.recv(BUFFER_SIZE)
            if (len(reply) > 0):
                # send to browser
                conn.send(reply)
            else:
                break
        s.close()
        conn.close()
    except socket.error, (value, message):
        s.close()
        conn.close()
        print ("Runtime Error:", message)
        sys.exit(1)

def printout(type,request,address):
    if "Request" in type:
        colornum = 92
    elif "Reset" in type:
        colornum = 93

    print "\033[",colornum,"m",address[0],"\t",type,"\t",request,"\033[0m"

def process_request(conn, client_addr):
    try:    
        # get the request from browser
        request = conn.recv(BUFFER_SIZE)

        # parse the first line
        first_line = request.split('\n')[0]

        # get url
        url = first_line.split(' ')[1]

        printout("Request",first_line,client_addr)

        # find the webserver and port
        http_pos = url.find("://")
        if (http_pos==-1):
            temp = url
        else:
            temp = url[(http_pos+3):]

        port_pos = temp.find(":")

        # find end of web server
        webserver_pos = temp.find("/")
        if webserver_pos == -1:
            webserver_pos = len(temp)

        webserver = ""
        port = -1
        if (port_pos==-1 or webserver_pos < port_pos):
            port = 80
            webserver = temp[:webserver_pos]
        else:       # specific port
            port = int((temp[(port_pos+1):])[:webserver_pos-port_pos-1])
            webserver = temp[:port_pos]
        
        #print "Connect to:", webserver, port

        proxy_server(conn, client_addr, request, webserver, port)
    except Exception, e:
        pass

try:
    listening_port = int(raw_input("Enter listeting port number: "))
except KeyboardInterrupt:
    print("\n")
    print("Ctrl-C pressed. Application shut down")
    sys.exit()

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #reuse the socket port
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', listening_port))
    s.listen(10)
    print("Socket initialized")
except Exception, e:
    print("Cannot initialize socket")
    sys.exit(2)

while True:
    try:
        conn, client_addr = s.accept()
        # create a thread to handle request
        thread.start_new_thread(process_request, (conn, client_addr))
    except KeyboardInterrupt:
        s.close()
        print("\n Proxy shut down")
        sys.exit(1)
s.close()