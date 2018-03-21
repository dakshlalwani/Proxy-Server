import socket
from threading import Thread
from signal import signal
from signal import SIGINT
from sys import exit
from urlparse import urlparse
from os import listdir, remove, path
import hashlib
from time import strptime, strftime, ctime, gmtime

config = {
    "HOST_NAME": "0.0.0.0",
    "BIND_PORT": 12345,
    "MAX_REQUEST_LEN": 1024,
    "CONNECTION_TIMEOUT": 5,
    "CACHE_SIZE": 3
}


class Server:
    def __init__(self, config):
        signal(SIGINT, self.shutdown)  # Shutdown on Ctrl+C
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a TCP socket
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Re-use the socket
        self.serverSocket.bind(
            (config['HOST_NAME'], config['BIND_PORT']))  # bind the socket to a public host, and a port
        self.serverSocket.listen(10)  # become a server socket
        self.__clients = {}

    def listenForClient(self):
        while True:
            (clientSocket, client_address) = self.serverSocket.accept()  # Establish the connection
            d = Thread(name=self._getClientName(client_address), target=self.proxy_thread,
                                 args=(clientSocket, client_address))
            d.setDaemon(True)
            d.start()
        self.shutdown(0, 0)

    def proxy_thread(self, conn, client_addr):
        print 'Connection established with server ', client_addr

        request = conn.recv(config['MAX_REQUEST_LEN'])  # get the request from browser
        first_line = request.split('\n')[0]  # parse the count line
        url = first_line.split(' ')[1]  # get url

        # find the webserver and port
        http_pos = url.find("://")  # find pos of ://
        if http_pos == -1:
            temp = url
        else:
            temp = url[(http_pos + 3):]  # get the rest of url

        port_pos = temp.find(":")  # find the port pos (if any)

        # find end of web server
        webserver_pos = temp.find("/")
        if webserver_pos == -1:
            webserver_pos = len(temp)

        webserver = ""
        port = -1

        if port_pos == -1 or webserver_pos < port_pos:  # default port
            port = 80
            webserver = temp[:webserver_pos]
        else:  # specific port
            port = int((temp[(port_pos + 1):])[:webserver_pos - port_pos - 1])
            webserver = temp[:port_pos]

        try:
            # create a socket to connect to the web server

            request = request.replace(request.split(' ')[1], urlparse(request.split(' ')[1]).__getattribute__('path'), 1)

            hash_object = hashlib.sha1(request.split(' ')[1].encode())
            cache_filename = hash_object.hexdigest() + ".cached"

            if path.exists(cache_filename):
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(config['CONNECTION_TIMEOUT'])
                s.connect((webserver, port))

                temp = request.split('\n')[0] + '\n'
                t = (strptime(ctime(path.getmtime(cache_filename)), "%a %b %d %H:%M:%S %Y"))
                tempreq = 'If-Modified-Since: ' + strftime('%a, %d %b %Y %H:%M:%S GMT', t)
                tempreq = temp + tempreq + '\n'
                for i in request.split('\n')[1:]:
                    tempreq = tempreq + i + '\n'

                s.sendall(tempreq)  # send request to webserver

                count = True

                while 1:
                    data = s.recv(config['MAX_REQUEST_LEN'])  # receive data from web server
                    if count:
                        if data.split(' ')[1] == '304':
                            print "File already exists in cache"
                        else:
                            o = open(cache_filename, 'wb')
                            print "File modified in cache"
                            if len(data) > 0:
                                o.write(data)
                            else:
                                break
                        count = False
                    else:
                        o = open(cache_filename, 'a')
                        if len(data) <= 0:
                            break
                        else:
                            o.write(data)
            else:
                print "File stored in cache"
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(config['CONNECTION_TIMEOUT'])
                s.connect((webserver, port))

                s.sendall(request)  # send request to webserver

                while 1:
                    data = s.recv(config['MAX_REQUEST_LEN'])  # receive data from web server
                    o = open(cache_filename, 'a')
                    if len(data) > 0:
                        o.write(data)
                    else:
                        break
                s.close()

            cache_counter = 0
            cacheFiles = []
            for file in listdir("."):
                if file.endswith(".cached"):
                    cache_counter += 1
                    cacheFiles.append(file)
            while cache_counter > config['CACHE_SIZE']:
                mint = gmtime()
                minf = cacheFiles[0]
                for fileName in cacheFiles:
                    cft = path.getmtime(fileName)
                    if cft < mint:
                        mint = cft
                        minf = fileName
                remove(minf)
                cache_counter = 0
                cacheFiles = []
                for file in listdir("."):
                    if file.endswith(".cached"):
                        cache_counter += 1
                        cacheFiles.append(file)

            data = open(cache_filename).readlines()
            data2 = ''.join(data)
            conn.send(data2)  # send to browser

            conn.close()
        except socket.error as error_msg:
            print 'ERROR: ', client_addr, error_msg
            if s:
                s.close()
            if conn:
                conn.close()

    def _getClientName(self, cli_addr):
        return "Client " + str(cli_addr)

    def shutdown(self, signum, frame):
        self.serverSocket.close()
        exit(0)


if __name__ == "__main__":
    server = Server(config)
    server.listenForClient()