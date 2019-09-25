#Our proxy implementation
import sys, socket, thread

BUFFER_SIZE = 8192
FORBIDDEN = ["SpongeBob", "Britney Spears", "Paris Hilton", "Norrk??ping"]

def parse(url):
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
    
    return (webserver, port)

def redirect(url):
    webserver, port = parse(url)
    return "HTTP/1.1 302 Found\r\nLocation: " + url + "\r\nHost: " + webserver + "\r\nConnection: close\r\n\r\n"

def proxy_server(conn, client_addr, request, webserver, port, isForbiddenUrl, needContentCheck):
    try:
        # create a socket to connect to the web server
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((webserver, port))

        if isForbiddenUrl:
            s.shutdown(socket.SHUT_RDWR)
            conn.shutdown(socket.SHUT_RD)
            conn.send(redirect("http://zebroid.ida.liu.se/error1.html"))
        else:
            s.send(request)         # send request to webserver

            while True:
                # receive data from web server
                reply = s.recv(BUFFER_SIZE)

                isBadContent = False

                if (len(reply) > 0):
                    if needContentCheck:
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
                                print("Bad content")
                                break 

                    if isBadContent:
                        conn.send(redirect("http://zebroid.ida.liu.se/error2.html"))
                    else:
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
    print address[0], "\t", type.upper(), "\t", request

def process_request(conn, client_addr):
    try:    
        # get the request from browser
        request = conn.recv(BUFFER_SIZE)

        # parse the first line
        first_line = request.split('\n')[0]

        # get url
        url = first_line.split(' ')[1]
        
        printout("Request",first_line,client_addr)

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
            printout("Forbidden", url, client_addr)
        
        #do we need to check the content
        needContentCheck = True
        notChecked = [".jpg", ".jpeg", ".gif", ".png", ".js", ".cs"]

        
        for x in notChecked:
            if url.endswith(x):
                needContentCheck = False
                break              

        # find the webserver and port
        webserver, port = parse(url)
        
        #print "Connect to:", webserver, port

        proxy_server(conn, client_addr, request, webserver, port, isForbiddenUrl, needContentCheck)
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