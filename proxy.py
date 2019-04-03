import sys
import socket
import os
import time
import signal
import threading


class Server:
    def __init__(self, config):

        lis = self.readBlckSite()
        for b_url in lis:
            config['BLACKLIST'].append(b_url)

        print(config['BLACKLIST'])

        self.con = config
        try:
            ''' trying to create socket '''
            self.servSckt = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
        except:
            # print("Server not created :( \n")
            sys.exit(0)

        try:
            ''' trying to reusing same socket '''
            self.servSckt.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except:
            # print("Error in reusing  :( \n")
            self.servSckt.close()
            sys.exit(0)

        try:
            ''' binding '''
            self.servSckt.bind((config['HOST_NAME'], config['BIND_PORT']))

        except:
            # print("Error in binding to local server  :( \n")
            self.servSckt.close()
            sys.exit(0)
        try:
            self.servSckt.listen(100)
            print("Server listening on PORT: "+str(config['BIND_PORT']))
        except:
            print("ERROR in listening port\n")
            sys.exit(0)

        while(True):
            try:
                (cSckt, cAddr) = self.servSckt.accept()
                try:
                    ''' creating thread '''
                    nThread = threading.Thread(
                        target=self.handleConn, args=(cSckt, cAddr))
                    nThread.start()
                except:
                    # print("error in creating thread:(\n")
                    self.servSckt.close()
                    sys.exit(0)

                # print("Working with "+string(cAddr)+" now!\n")

            except:
                print("Error in accepting connection \n")
                self.servSckt.close()
                sys.exit(0)

    def parsing_req(self, creq, cAddr):
        try:
            xx = creq.split('\n')[0]
            zz = xx.split(' ')
            full_url = zz[1]
            method = zz[0]
            poshttp = full_url.find("://")
            protocol = "http"
            if poshttp == -1:
                protocol = full_url[:poshttp]
            else:
                full_url = full_url[(poshttp+3):]

            wserv = full_url.find("/")
            if wserv == -1:
                wserv = len(full_url)
            posport = full_url.find(":")

            s_webserv = ""
            if(posport == -1 or wserv < posport):
                port = 80
                s_webserv = full_url[:wserv]
            else:
                port = int(full_url[(posport+1):wserv])
                s_webserv = full_url[:posport]

            data = creq.splitlines()
            auth = []
            for i in data:
                if "Authorization" in i:
                    auth.append(i)

            if len(auth) > 0:
                auth_val = auth[0].split()[2]
            else:
                auth_val = None

            zz[1] = full_url[wserv:]
            data[0] = ' '.join(zz)
            ccdd = "\r\n".join(data)+'\r\n\r\n '

            ret_obj = {
                "S_PORT": port,
                "S_URL": s_webserv,
                "C_DATA": ccdd,
                "PROTOCOL": protocol,
                "URL": full_url,
                "METHOD": method,
                "AUTH": auth_val,
            }
            return ret_obj
        except:
            print("Error in parsing\n")
            return None

    def handleConn(self, conn, cAddr):
        try:
            ''' getting request '''
            crequest = conn.recv(self.con['MAX_REQUEST_LEN'])
        except:
            print("error in recieving request\n")
            self.servSckt.close()
            conn.close()
            return

        req = self.parsing_req(str(crequest), cAddr)

        if not req:
            self.servSckt.close()
            conn.close()
            return

        print(req)

        # if flag == 0:
#        self.new_connection(crequest, port, s_webserv, conn)

    def readBlckSite(self):
        ''' for fetching blacklisted url '''
        try:
            f = open("proxy/blacklist.txt", "r")
        except:
            print("Error: proxy/blacklist.txt not opening \n")

        z = [i.rstrip(' \n') for i in f.readlines()]

        try:
            f.close()
        except:
            print("Error in closing.\n")

        return z

        # configuration
confi = {
    'HOST_NAME': '127.0.0.1',
    'MAX_REQUEST_LEN': 100000,
    'CONNECTION_TIMEOUT': 10,
    'BIND_PORT': 20100,
    'BLACKLIST': [],
}

ris_server = Server(confi)
