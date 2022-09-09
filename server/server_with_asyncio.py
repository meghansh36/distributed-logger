import asyncio
import sys
from utils import Utils
from common import Common
import os

log_file = 'logs/machine.log'

connected_clients = {}

async def handle_client_task(reader, writer, client_addr):
    while True:
        data = await reader.read(Common.MAX_QUERY_SIZE)
        if data == b'':
            print("Close the connection")
            writer.close()
            break
        
        query = data.decode()
        print(f"Got query from {client_addr}: {query}")
        return_code, cmds = Common.prepare_grep_shell_cmds(query, log_file)
        
        if return_code == 1:
            print(f"response: {cmds[0].decode()}")
            writer.write(cmds[0])
        else:
            output = b''

            # logic to add file names and match count for all the files
            if os.path.isfile(log_file):
                output = bytes(log_file, 'utf-8')
                output += b': '

            line_count = Utils.execute_shell(cmds[0].decode())
            if os.path.isfile(log_file):
                output += line_count
                output = output.decode().split('/')[-1]
                output = output.strip().encode()
                output += b'\n'
            else:
                files = line_count.decode().splitlines()
                output += files[0].split('/')[-1].strip().encode()
                for file in files[1:]:
                    output += b','
                    output += file.split('/')[-1].strip().encode()
                output += b'\n'
            
            print(f'{output}')

            logs = Utils.execute_shell(cmds[1].decode())
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


async def start_server(hostname, port):
    server = await asyncio.start_server(
        handle_client, hostname, port)

    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    print(f'Serving on {addrs}')

    async with server:
        await server.serve_forever()


def main(hostname, port):

    # start server
    asyncio.run(start_server(hostname, port))


if __name__ == "__main__":

    hostname, port, log_file = Common.parse_server_cmdline_args(sys.argv[1:])

    main(hostname, port)