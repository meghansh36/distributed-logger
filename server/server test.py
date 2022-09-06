import asyncio
import getopt
from typing import List, Tuple, final
import sys
from utilities import prepare_grep_shell_cmds, execute_shell
import os

MAX_QUERY_SIZE: final = 5120
hostname = '127.0.0.1'
port = 8000
log_file = 'logs/machine.log'
connected_clients = {}

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

async def handle_client_task(reader, writer, client_addr):
    while True:
        data = await reader.read(MAX_QUERY_SIZE)
        if data == b'':
            print("Close the connection")
            writer.close()
            break
        
        query = data.decode()
        print(f"Got query from {client_addr}: {query}")
        return_code, cmds = prepare_grep_shell_cmds(query, log_file)
        
        if return_code == 1:
            print(f"response: {cmds[0].decode()}")
            writer.write(cmds[0])
        else:
            output = b''

        # logic to add file names and match count for all the files
            if os.path.isfile(log_file):
                output = bytes(log_file, 'utf-8')
                output += b': '

            line_count = execute_shell(cmds[0].decode())
            if os.path.isfile(log_file):
                output += line_count
            else:
                files = line_count.decode().splitlines()
                output += files[0].encode()
                for file in files[1:]:
                    output += b','
                    output += file.encode()
                output += b'\n'
            
            print(f'{output}')

            logs = execute_shell(cmds[1].decode())
            output += logs
            print(f"sending {len(output)} bytes")
            writer.write(output)

        await writer.drain()

    

async def handle_client(reader, writer):

    # add logic here to keep track of all connected clients
    client_socket = writer.get_extra_info('socket')
    client_addr = writer.get_extra_info('peername')
    connected_clients[client_socket] = client_addr
    print(connected_clients)

    await handle_client_task(reader, writer, client_addr)
    del connected_clients[client_socket]
    print(connected_clients)


async def main():
    server = await asyncio.start_server(
        handle_client, hostname, port)

    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    print(f'Serving on {addrs}')

    async with server:
        await server.serve_forever()

asyncio.run(main())