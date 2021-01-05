import socket
import os
import sys
import argparse
import time
import datetime
import signal
import random
from urllib.parse import urlparse

# Define a constant for our buffer size

BUFFER_SIZE = 1024
TIMEOUT_TIME = 300

# Signal handler for graceful exiting.

def signal_handler(sig, frame):
    print('Interrupt received, shutting down ...')
    sys.exit(0)

# A function for creating HTTP GET messages.

def prepare_get_message(host, port, file_name):
    request = f'GET {file_name} HTTP/1.1\r\nHost: {host}:{port}\r\n\r\n' 
    return request

# Read a single line (ending with \n) from a socket and return it.
# We will strip out the \r and the \n in the process.

def get_line_from_socket(sock):

    done = False
    line = ''
    while (not done):
        char = sock.recv(1).decode()
        if (char == '\r'):
            pass
        elif (char == '\n'):
            done = True
        else:
            line = line + char
    return line

# Read a file from the socket and print it out.  (For errors primarily.)

def print_file_from_socket(sock, bytes_to_read):

    bytes_read = 0
    while (bytes_read < bytes_to_read):
        chunk = sock.recv(BUFFER_SIZE)
        bytes_read += len(chunk)
        print(chunk.decode())

# Read a file from the socket and save it out.

def save_file_from_socket(sock, bytes_to_read, file_name):

    with open(file_name, 'wb') as file_to_write:
        bytes_read = 0
        while (bytes_read < bytes_to_read):
            chunk = sock.recv(BUFFER_SIZE)
            bytes_read += len(chunk)
            file_to_write.write(chunk)

# Send the given response and file back to the client.

def send_response_to_client(sock, code, file_name):

    # Determine content type of file

    if ((file_name.endswith('.jpg')) or (file_name.endswith('.jpeg'))):
        type = 'image/jpeg'
    elif (file_name.endswith('.gif')):
        type = 'image/gif'
    elif (file_name.endswith('.png')):
        type = 'image/jpegpng'
    elif ((file_name.endswith('.html')) or (file_name.endswith('.htm'))):
        type = 'text/html'
    else:
        type = 'application/octet-stream'
    
    # Get size of file

    file_size = os.path.getsize(file_name)

    # Construct header and send it

    header = prepare_response_message(code) + 'Content-Type: ' + type + '\r\nContent-Length: ' + str(file_size) + '\r\n\r\n'
    sock.send(header.encode())

    # Open the file, read it, and send it

    with open(file_name, 'rb') as file_to_send:
        while True:
            chunk = file_to_send.read(BUFFER_SIZE)
            if chunk:
                sock.send(chunk)
            else:
                break

# Send redirection response to client

def send_redirection_to_client(sock, code, file_name, host, port):

    # Determine content type of file

    if ((file_name.endswith('.jpg')) or (file_name.endswith('.jpeg'))):
        type = 'image/jpeg'
    elif (file_name.endswith('.gif')):
        type = 'image/gif'
    elif (file_name.endswith('.png')):
        type = 'image/jpegpng'
    elif ((file_name.endswith('.html')) or (file_name.endswith('.htm'))):
        type = 'text/html'
    else:
        type = 'application/octet-stream'
    
    # Get size of file

    file_size = os.path.getsize(file_name)

    # Construct header and send it

    header = prepare_response_message(code) + 'Location: '  + host + ':' + str(port) + '\r\nContent-Type: ' + type + '\r\nContent-Length: ' + str(file_size) + '\r\n\r\n'
    sock.send(header.encode())

    # Open the file, read it, and send it

    with open(file_name, 'rb') as file_to_send:
        while True:
            chunk = file_to_send.read(BUFFER_SIZE)
            if chunk:
                sock.send(chunk)
            else:
                break

# Create an HTTP response

def prepare_response_message(value):
    date = datetime.datetime.now()
    date_string = 'Date: ' + date.strftime('%a, %d %b %Y %H:%M:%S EDT')
    message = 'HTTP/1.1 '
    if value == '200':
        message = message + value + ' OK\r\n' + date_string + '\r\n'
    elif value == '404':
        message = message + value + ' Not Found\r\n' + date_string + '\r\n'
    elif value == '501':
        message = message + value + ' Method Not Implemented\r\n' + date_string + '\r\n'
    elif value == '505':
        message = message + value + ' Version Not Supported\r\n' + date_string + '\r\n'
    elif value == '301':
        message = message + value + ' Moved Permanently\r\n' + date_string + '\r\n'

    return message

# Reads the list of server adresses from the filename provided 

def generate_balanced_load(filename):

    f = open(filename)
    server_entry = 0
    server_address = []

    for x in f:

        try:

            # print(x.rstrip())
            parsed_url = x.split(":")
            
            if((parsed_url[0] == None) or (parsed_url[1] == None)):
                raise ValueError

            server_address.append(parsed_url)
            server_entry = server_entry + 1

        except ValueError:
            print('Error: Invalid address, ensure the server adresses in the config file are of the form host:port')
            sys.exit(1)
        
    # Now we run the performance test for the array of server addresses to determine their response time

    servers = []
    server_entry = 0

    for address in server_address:

        # Now we try to make a connection to the current server 

        print('Connecting to server ' + address[0] + ':' + address[1] + ' for a performance test...')

        try:

            testing_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            testing_socket.connect((address[0], int(address[1])))

            # The connection was successful, so we can send our test message

            print("Connection to server established. Sending message to test response time..\n")
            message = prepare_get_message(address[0], int(address[1]), 'testing.jpg')

            # Start timer and send the message

            start_time = time.perf_counter()
            testing_socket.send(message.encode())

            # Recieve the response from the server and take a look at it

            response_line = get_line_from_socket(testing_socket)
            response_list = response_line.split(' ')
            headers_done = False

            # If an error is returned from the server, we dump everything sent and exit

            if (response_list[1] != '200'):
                print('Error:  An error response was received from the server.  Details:\n')
                print(response_line);
                bytes_to_read = 0
                while (not headers_done):
                    header_line = get_line_from_socket(testing_socket)
                    print(header_line)
                    header_list = header_line.split(' ')
                    if (header_line == ''):
                        headers_done = True
                    elif (header_list[0] == 'Content-Length:'):
                        bytes_to_read = int(header_list[1])
                print_file_from_socket(testing_socket, bytes_to_read)
                sys.exit(1)

            # if its OK, we retieve and write the file out.

            else:

                print('Success:  Server is sending file.  Downloading it now.')

                # Go through headers and find the size of the file, then save it.
        
                bytes_to_read = 0
                while (not headers_done):
                    header_line = get_line_from_socket(testing_socket)
                    header_list = header_line.split(' ')
                    if (header_line == ''):
                        headers_done = True
                    elif (header_list[0] == 'Content-Length:'):
                        bytes_to_read = int(header_list[1])
                save_file_from_socket(testing_socket, bytes_to_read, 'testing.jpg')

            # Stop the timer after the file has been saved

            end_time = time.perf_counter()

            # print("server " + address[0] + ':' + address[1] + " responded in " + str(end_time-start_time) + " units of time")

            servers.append(server_data(address[0], int(address[1]), (end_time - start_time)))


        except ConnectionRefusedError:

            print('Error: server' + address[0] + ':' + address[1] + ' was not accepting connections.')

    # Sort the array of servers from fastest response time to slowest response time

    newlist = sorted(servers, key=lambda x: x.response_time, reverse=True)

    # Create the array that will baance the requests

    balanced_load = []
    request_ratio = 1
    for x in newlist:
        for i in range(request_ratio):
            balanced_load.append(x)
        request_ratio = request_ratio + 1 

    return balanced_load

# Class to hold server address and rsponse time

class server_data:
    def __init__(self, host, port, response_time):
        self.host = host
        self.port = port
        self.response_time = response_time
        
# Our main function

def main():

    # Check command line arguments to retrieve a config file confaining the server host:port info

    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="File containing the host:port for all of the servers")
    args = parser.parse_args()

    # generate the balanced array of servers to manage client requests efficiently

    balanced_load = generate_balanced_load(args.config)

    # Display the request_ratio array
    
    print("\nBelow is the load balancing array of servers:")
    for x in balanced_load:
        print("Server " + x.host + ":" + str(x.port) + ' RT: ' + str(x.response_time))

    # DEFINETLEY WORKS UP TO HERE

    # The load balancer can now accept client requests
    # Register our signal handler for shutting down.

    signal.signal(signal.SIGINT, signal_handler)

    # Create the socket.  We will ask this to work on any interface and to pick
    # a free port at random.  We'll print this out for clients to use.

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.settimeout(TIMEOUT_TIME)
    server_socket.bind(('', 0))
    print('Will wait for client connections at port ' + str(server_socket.getsockname()[1]))
    server_socket.listen(1)
    
    # Keep the server running forever.
    
    while(1):

        try:
            print('Waiting for incoming client connection ...')
            conn, addr = server_socket.accept()
            print('Accepted connection from client address:', addr)
            print('Connection to client established, waiting to receive message...')

            # We obtain our request from the socket.  We look at the request and
            # figure out what to do based on the contents of things.

            request = get_line_from_socket(conn)
            print('Received request:  ' + request)
            request_list = request.split()

            # This server doesn't care about headers, so we just clean them up.

            while (get_line_from_socket(conn) != ''):
                pass

            # If we did not get a GET command respond with a 501.

            if request_list[0] != 'GET':
                print('Invalid type of request received ... responding with error!')
                send_response_to_client(conn, '501', '501.html')

            # If we did not get the proper HTTP version respond with a 505.

            elif request_list[2] != 'HTTP/1.1':
                print('Invalid HTTP version received ... responding with error!')
                send_response_to_client(conn, '505', '505.html')

            # We have the right request and version, so check if file exists.
                    
            else:

                # Select a server from the balanced_load array to redirect the client to

                selected_server = balanced_load[random.randint(0,len(balanced_load)-1)]

                send_redirection_to_client(conn,'301','301.html',selected_server.host,selected_server.port)

            # We are all done with this client, so close the connection and
            # Go back to get another one!

            conn.close();

        except OSError:

            print("\nBelow is the load balancing array of servers:")
            balanced_load = generate_balanced_load(args.config)

            for x in balanced_load:
                print("Server " + x.host + ":" + str(x.port) + ' RT: ' + str(x.response_time))



if __name__ == '__main__':
    main()
