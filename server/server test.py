import asyncio
import getopt
from typing import List, Tuple, final
import sys
from utilities import prepare_shell_cmd, execute_shell

MAX_QUERY_SIZE: final = 5120
hostname = '127.0.0.1'
port = 8000
log_file = '../test_logs/HDFS_2K.log'
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
        return_code, cmd = prepare_shell_cmd(query, log_file)
        
        if return_code == 1:
            print(f"response: {cmd.decode()}")
            writer.write(cmd)
        else:
            output = execute_shell(cmd)
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