import sys
import socket
import os
import time
import signal
import threading
import base64
import json
import datetime


class Server:
    def __init__(self, config):

        lis = self.readBlckSite()
        for b_url in lis:
            config['BLACKLIST'].append(b_url)
        self.cache_size = 3
        self.occ_cache = 2
        self.cache_dir = "./cache"
        lis = self.readAuthSite()
        for b_url in lis:
            config['AUTH'].append(base64.b64encode(
                b_url.encode('utf-8')).decode('utf-8'))

        print(config['BLACKLIST'])
        print(config['AUTH'])

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

        if not os.path.isdir(self.cache_dir):
            os.makedirs(self.cache_dir)
        for file in os.listdir(self.cache_dir):
            os.remove(self.cache_dir + "/" + file)

        while(True):
            try:
                (cSckt, cAddr) = self.servSckt.accept()
                try:
                    ''' creating thread '''
                    nThread = threading.Thread(
                        target=self.handleConn, args=(cSckt, cAddr))
                    nThread.start()
                except:
                    self.servSckt.close()
                    sys.exit(0)


            except:
                print("Error in accepting connection \n")
                self.servSckt.close()
                sys.exit(0)


    def add_log(self, fileurl, cAddr):
        fileurl = fileurl.replace("/", "__")
        if not fileurl in logs:
            logs[fileurl] = []
        dt = time.strptime(time.ctime(), "%a %b %d %H:%M:%S %Y")
        logs[fileurl].append({
            "datetime": dt,
            "client": json.dumps(cAddr),
        })

    def do_cache_or_not(self, fileurl):
        try:
            log_arr = logs[fileurl.replace("/", "__")]
            if len(log_arr) < self.occ_cache:
                return False
            last_third = log_arr[len(log_arr)-self.occ_cache]["datetime"]
            if datetime.datetime.fromtimestamp(time.mktime(last_third)) + datetime.timedelta(minutes=5) >= datetime.datetime.now():
                return True
            else:
                return False
        except Exception as e:
            print(e)
            return False

    def get_current_cache_info(self, fileurl):
        if fileurl.startswith("/"):
            fileurl = fileurl.replace("/", "", 1)

        cache_path = self.cache_dir + "/" + fileurl.replace("/", "__")

        if os.path.isfile(cache_path):
            last_mtime = time.strptime(time.ctime(
                os.path.getmtime(cache_path)), "%a %b %d %H:%M:%S %Y")
            return cache_path, last_mtime
        else:
            return cache_path, None

    def get_cache_req(self, client_addr, req):
        self.add_log(req["URL"], client_addr)
        do_cache = self.do_cache_or_not(req["URL"])
        cache_path, last_mtime = self.get_current_cache_info(
            req["URL"])
        req["do_cache"] = do_cache
        req["cache_path"] = cache_path
        req["last_mtime"] = last_mtime
        return req


    def parsing_req(self, creq, cAddr):
        try:

            data = creq.splitlines()
            while data[len(data)-1] == '':
                data.remove('')
            zz = data[0].split()
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
            zz[1] = full_url[wserv:]
            s_webserv = ""
            if  wserv < posport :
                s_webserv, port = full_url[:wserv] , 80
            elif posport == -1 :
                s_webserv, port = full_url[:wserv] , 80
            else:
                port = int((full_url[(posport+1):])[:wserv-posport-1])
                s_webserv = full_url[:posport]

            auth = []              
            auth_val = None
            for i in data:
                if "Authorization" in i:
                    auth.append(i)

            if len(auth) > 0:
                auth_val = auth[0].split()[5]
                pos = auth_val.find("\\")
                auth_val = auth_val[:pos]


            
            data[0] = ' '.join(zz)
            creq = "\r\n".join(data) + '\r\n\r\n'

            print(s_webserv)
            ret_obj = {
                "S_PORT": port,
                "S_URL": s_webserv,
                "C_DATA": creq,
                "PROTOCOL": protocol,
                "URL": full_url,
                "METHOD": method,
                "AUTH": auth_val,
            }
            return ret_obj
        except Exception as e :
            print("Error in parsing\n")
            print e
            return 

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

        flag = 1
        if (str(req["S_URL"])+":"+str(req["S_PORT"])) in self.con["BLACKLIST"]:
            if not (str(req["AUTH"]) in self.con["AUTH"]) or not req["AUTH"]:
                flag = 0

        if flag == 0:
            conn.send(b"HTTP/1.0 200 OK\r\n")
            conn.send(b"Content-Length: 39\r\n")
            conn.send(b"\r\n")
            conn.send(b"USER NOT AUTHORIZED TO ACCESS THIS!! \r\n")
            conn.close()
            return

        if "POST" in req["METHOD"]: 
            self.post_method(conn, req)

        elif "GET" in req["METHOD"]:
            req = self.get_cache_req(cAddr, req)
            if req["last_mtime"]:
                ini = req["C_DATA"].splitlines()
                while ini[len(ini)-1] == '':
                    ini.remove('')
                ini.append("If-Modified-Since: " + time.strftime("%a %b %d %H:%M:%S %Y", req["last_mtime"]))
                req["C_DATA"] = "\r\n".join(ini) + "\r\n\r\n"
            self.get_method(conn, req)
        else:
            conn.send(b"HTTP/1.0 200 OK\r\n")
            conn.send(b"Content-Length: 20\r\n")
            conn.send(b"\r\n")
            conn.send(b"USE GET OR POST!! \r\n")
            conn.close()
            return

    def get_method(self, conn, req):
        do_cache = req["do_cache"]
        cache_path = req["cache_path"]
        last_mtime = req["last_mtime"]
        print(req["cache_path"])

        try:
            ''' trying to create socket '''
            new_sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except:
            print("Request server not created :( \n")
            conn.close()
            return

        try:
            ''' connecting  '''
            new_sckt.connect((req["S_URL"], req["S_PORT"]))

        except:
            # print("Error in binding to local server  :( \n")
            new_sckt.close()
            conn.close()
            return
        print("hii")

        new_sckt.send(req["C_DATA"].encode())
        try:
            data = new_sckt.recv(4096)
            print("--------")
            print(data)
            print("--------s")
            if last_mtime and "304 Not Modified" in data:
                print("returning cached file")
                f = open(cache_path, 'rb')
                chunk = f.read(4096)
                while chunk:
                    conn.send(chunk)
                    chunk = f.read(4096)
                f.close()
        
            else:
                if do_cache:
                    print("caching file!!")
                    f = open(cache_path, "w+")
                    while len(data):
                        conn.send(data)
                        f.write(data)
                        data = new_sckt.recv(4096)
                    f.close()
                    conn.send("\r\n\r\n")
                else:
                    print("without caching!!")
                    while len(data):
                        conn.send(data)
                        data = new_sckt.recv(4096)
                    conn.send("\r\n\r\n")

            new_sckt.close()
            conn.close()
            return

        except:

            conn.close()
            return

    def post_method(self, conn, req):
        try:
            ''' trying to create socket '''
            new_sckt = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
        except:
            print("Request server not created :( \n")
            conn.close()
            return

        try:
            ''' connecting  '''
            new_sckt.connect((req["S_URL"], config["S_PORT"]))

        except:
            # print("Error in binding to local server  :( \n")
            new_sckt.close()
            conn.close()
            return
        try:
            new_sckt.send(req["C_DATA"].encode("utf-8"))
            while(True):
                xx = new_sckt.recv(4096)
                if len(xx):
                    conn.send(xx)
                else:
                    break

                new_sckt.close()
                conn.close()
                return
        except:
            new_sckt.close()
            conn.close()
            return

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

    def readAuthSite(self):
        ''' for fetching authorized username/password '''
        try:
            f = open("proxy/auth.txt", "r")
        except:
            print("Error: proxy/auth.txt not opening \n")

        z = [i.rstrip(' \n') for i in f.readlines()]

        try:
            f.close()
        except:
            print("Error in closing.\n")

        return z


# configuration
confi = {
    'HOST_NAME': '127.0.0.1',
    'MAX_REQUEST_LEN': 5000,
    'CONNECTION_TIMEOUT': 10,
    'BIND_PORT': 20100,
    'BLACKLIST': [],
    'AUTH': [],
}

locks = {}
logs = {}
ris_server = Server(confi)
