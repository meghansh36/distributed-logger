#!/opt/homebrew/bin/python3
import sys
import os
import getopt
import subprocess
import ast
import socket
import selectors
from typing import List, Tuple, final
from selectors import SelectorKey


def execute_shell(cmd: str) -> str:
    # execute grep command using shell
    grep = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, shell=True)
    stdout, stderr = grep.communicate()
    if len(stderr) == 0:
        return stdout
    else:
        print(f"grep command {cmd} failed with error: {stderr}")
        return b'failed to retrive logs'


def prepare_shell_cmd(query: str, logpath: str) -> Tuple[int, List[str]]:
    query_prefix = "search "

    if not query.startswith(query_prefix):
        return (1, str.encode("invalid query: expected search ['<query string 1>', '<query string 2>']"))

    try:
        search_strings = ast.literal_eval(query[len(query_prefix):])
        cmds = []
        cmd = "grep -c "
        for search_string in search_strings:
            cmd += f"-e '{search_string}' "
        cmd += logpath
        cmds.append(cmd)

        cmd = "grep "
        for search_string in search_strings:
            cmd += f"-e '{search_string}' "
        cmd += logpath
        cmds.append(cmd)

        return (0, cmds)
    except:
        return (1, str.encode("invalid query: expected search ['<query string 1>', '<query string 2>']"))


def socket_send_bytes(sock, data) -> None:
    try:
        sock.sendall(data)
    except:
        print('failed to send')


def process_query(query, log_file):
    return_code, cmds = prepare_shell_cmd(query, log_file)
    if return_code == 1:
        print(f"response: {cmds.decode()}")
        return cmds
    else:
        output = b''
        if os.path.isfile(log_file):
            output = bytes(log_file, 'utf-8')
            output += b': '

        line_count = execute_shell(cmds[0])
        output += line_count

        logs = execute_shell(cmds[1])
        output += logs
        print(f"sending {len(output)} bytes")
        return output


if __name__ == "__main__":
    MAX_QUERY_SIZE: final = 5120

    hostname = '127.0.0.1'
    port = 8000
    log_file = 'logs/machine.log'

    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:p:l:", [
            "hostname=", "port=", "help=", "logfile="])

        for opt, arg in opts:
            if opt == '--help':
                print('server.py -h <hostname> -p <port>')
                sys.exit()
            elif opt in ("-h", "--hostname"):
                hostname = arg
            elif opt in ("-p", "--port"):
                port = int(arg)
            elif opt in ("-l", "--logfile"):
                log_file = arg

    except getopt.GetoptError:
        print('server.py -h <hostname> -p <port>')
        sys.exit(2)

    server_address = (hostname, port)

    # creating socket to listen for requests for searching logs
    log_query_socket = socket.socket()

    log_query_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # configure socket as non-blocking
    log_query_socket.setblocking(False)

    # bind and listen for connections
    log_query_socket.bind(server_address)
    log_query_socket.listen()

    # using selector to use OS event notification interface for monitoring events on socket fd
    selector = selectors.DefaultSelector()

    # register log_query_socket for READ events
    selector.register(log_query_socket, selectors.EVENT_READ)

    # dict to track clients
    clients = {}

    # main loop for handling requests
    while True:

        # wait for events on registerd socket FDs for 1 second
        events: List[Tuple[SelectorKey, int]] = selector.select(timeout=1)

        if len(events) == 0:  # select timer expired no notifications from socket FDs
            continue

        for event, mask in events:

            # Get socket from SelectorKey
            event_socket = event.fileobj

            if event_socket == log_query_socket:
                # READ event from server socket must be client connection
                client_connection, address = log_query_socket.accept()
                # mark client connection as non-blocking
                client_connection.setblocking(False)
                print(f"Got a connection from {address}")
                # register client connection for event notification
                selector.register(client_connection, selectors.EVENT_READ)
                # store the connection details into a dict
                clients[client_connection] = address
            else:
                data = event_socket.recv(MAX_QUERY_SIZE)

                if len(data) > 0:
                    print(f"Got query from {clients[event_socket]}: {data}")
                    output = process_query(data.decode(), log_file)
                    socket_send_bytes(event_socket, output)
                else:  # empty data indicates that client has closed the connection
                    print(f"client {clients[event_socket]} closed connection")

                print(f"closing client connection: {clients[event_socket]}")
                # unregister client connection for notifications
                selector.unregister(event_socket)
                # remove from stored clients
                del clients[event_socket]
                # close connection
                event_socket.close()
