import asyncio
import sys
from utils import execute_shell
from common import MAX_QUERY_SIZE, prepare_grep_shell_cmds, parse_server_cmdline_args
import os

hostname = '127.0.0.1'
port = 8000
log_file = 'logs/machine.log'

connected_clients = {}

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
        writer.close()


async def handle_client(reader, writer):

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


if __name__ == "__main__":

    hostname, port, log_file = parse_server_cmdline_args(sys.argv[1:])

    # start server
    asyncio.run(main())