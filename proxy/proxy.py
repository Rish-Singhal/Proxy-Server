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
            sys.exit(0)

        try:
            ''' binding '''
            self.servSckt.bind((config['HOST_NAME'], config['BIND_PORT']))

        except:
            # print("Error in binding to local server  :( \n")
            sys.exit(0)

        self.servSckt.listen(100)

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
                    # print("error in creating thread:(\n")
                    sys.exit(0)

                # print("Working with "+string(cAddr)+" now!\n")

            except:
                print("Error in accepting connection \n")
                sys.exit(0)

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
