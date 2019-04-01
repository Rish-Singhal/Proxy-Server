import sys
import socket
import os
import time
import signal
import threading


class Server:
    def __init__(self, config):
        self.con = config
        try:
            ''' trying to create socket '''
            self.servSckt = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
        except:
            print("Server not created :( \n")
            sys.exit(0)

        try:
            ''' trying to reusing same socket '''
            self.servSckt.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except:
            print("Error in reusing  :( \n")
            sys.exit(0)

        try:
            ''' binding '''
            self.servSckt.bind((config['HOST_NAME'], config['BIND_PORT']))

        except:
            print("Error in binding to local server  :( \n")
            sys.exit(0)
        self.servSckt.listen(5)
        # try:
        #     ''' listening '''
        #     self.servSckt.listen(5)
        #     print("server listening at port " +
        #           string(config['BIND_PORT']+"\n"))
        # except:
        #     print("error in listening :(\n")
        #     sys.exit(0)

        while(True):
            try:
                (cSckt, cAddr) = self.servSckt.accept()
                try:
                    ''' creating thread '''
                    nThread = threading.Thread(
                        target=self.handleConn, args=(cSckt, cAddr))
                    nThread.setDaemon(True)
                    nThread.start()
                except:
                    print("error in creating thread:(\n")
                    sys.exit(0)

                print("Working with "+string(cAddr)+" now!\n")

            except:
                print("Error in accepting connection\n")

    def handleConn(self, conn, cAddr):
        try:
            ''' getting request '''
            crequest = conn.recv(self.con['MAX_REQUEST_LEN'])
        except:
            print("error in recieving request\n")

        full_url = crequest.split(' ')[0]
        poshttp = full_url.find("://")

        if poshttp == -1:
            x = full_url
        else:
            x = full_url[(poshttp+3):]

        wserv = x.find("/")
        if wserv == -1:
            wserv = len(x)
        posport = x.find(":")

        s_webserv = ""
        if(posport == -1 or wserv > posport):
            port = 80
            s_webserv = x[:wserv]
        else:
            port = int((x[(posport+1):])[:wserv-posport-1])
            s_webserv = x[:posport]

        self.new_connection(self, crequest, port, s_webserv, conn)

    def new_connection(self, crequest, port, s_webserv, conn):
        try:
            ''' creating new socket for the connection '''
            sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except:
            print("Error in creating socket for connection .\n")

        try:
            ''' setting timeout '''
            sckt.settimeout(self.con['CONNECTION_TIMEOUT'])
        except:
            print("Error in seeting timeout .\n")

        try:
            ''' connecting the new socket '''
            sckt.connect((s_webserv, port))
        except:
            print("Error in connecting socket for new connection .\n")

        try:
            ''' sending request to all '''
            sckt.sendall(crequest)
        except:
            print("Error in sending request :( \n")

        while(True):
            ''' passing the data via proxy server '''
            try:
                ''' recieve data '''
                in_data = sckt.recv(self.con['MAX_REQUEST_LEN'])
            except:
                print("error in recieving data\n")

            if len(in_data) > 0:
                ''' sending data '''
                conn.send(in_data)
            else:
                break

        self.cclose(self, conn)

    def cclose(self, conn):
        print("Closig connection now. ")
        try:
            conn.close()
        except:
            print("Error in closing connection\n")
            sys.exit(0)


# configuration
confi = {
    'HOST_NAME': '127.0.0.1',
    'MAX_REQUEST_LEN': 100000,
    'CONNECTION_TIMEOUT': 10,
    'BIND_PORT': 20100
}

ris_server = Server(confi)
