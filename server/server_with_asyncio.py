import asyncio
import sys
from utils import Utils
from common import Common
import os


"""
Main Class for Running a Server
"""
class ServerWithAsyncio :
    # Dictionary to keep track of connected clients
    connected_clients = {}
    
    # Constructor function to set hostname, port and log file path
    def __init__(self,hostname, port, log_file):
        self.hostname = hostname
        self.port = port
        self.log_file = log_file

    """
    Main function to process client query. 
    
    @params reader: Reader object for connected client
    @params writer: Writer object for connected client
    @params client_addr: Address metadata of the connected client
    """
    async def handle_client_task(self, reader, writer, client_addr):

        while True:
            # Read query from client
            data = await reader.read(Common.MAX_QUERY_SIZE)
            # If there is no data, close the connection and exit
            if data == b'':
                print("Close the connection")
                writer.close()
                break
            
            # Decode the query
            query = data.decode()
            print(f"Got query from {client_addr}: {query}")

            # Call function to parse client query and prepare the grep command
            return_code, cmds = Common.prepare_grep_shell_cmds(query, self.log_file)
            
            # If retrun code is error code, send error response to server
            if return_code == 1:
                print(f"response: {cmds[0].decode()}")
                writer.write(cmds[0])
            # If return code is a success code, execute grep command on shell
            else:
                output = b''

                # logic to add file names and match count for all the files
                if os.path.isfile(self.log_file):
                    output = bytes(self.log_file, 'utf-8')
                    output += b': '
                
                # ??? what does this do?
                line_count = Utils.execute_shell(cmds[0].decode())
                if os.path.isfile(self.log_file):
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

                # Till now, the output contains only the line match counts
                # Now, we execute another grep command to fetch the actual match lines

                logs = Utils.execute_shell(cmds[1].decode())
                output += logs
                print(f"sending {len(output)} bytes")

                # Add output to the buffer
                writer.write(output)

            # Drain buffer and send the output to the server
            await writer.drain()
            # Close the connection
            writer.close()

    """
    This function is a callback function and is run as soon as a client connects to the server.

    @params reader: Reader object for read operations on client socket
    @params writer: Writer object for write operations on client socket
    """
    async def handle_client(self, reader, writer):
        # Get client metadata
        client_socket = writer.get_extra_info('socket')
        client_addr = writer.get_extra_info('peername')
        # Add client in the connected clients dictionary
        self.connected_clients[client_socket] = client_addr
        print(self.connected_clients)

        # Call function to read and process client query and wait till its complete
        await self.handle_client_task(reader, writer, client_addr)
        # After successful completion and disconnection, delete the client from the connected clients dict.
        del self.connected_clients[client_socket]
        print(self.connected_clients)

    """
    Function to start server
    """
    async def start_server(self):
        # Call asyncio start_server function and provide a callback function, hostname and port
        server = await asyncio.start_server(
            self.handle_client, self.hostname, self.port)

        addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
        print(f'Serving on {addrs}')

        # Keep the server running forever and actively listening for client connections
        async with server:
            await server.serve_forever()

    
    def main(self):

        # start server
        asyncio.run(self.start_server())


if __name__ == "__main__":

    # Parse command line arguments and extract hostname, port and log file path from the user provided values
    hostname, port, log_file = Common.parse_server_cmdline_args(sys.argv[1:])
    # Instantiate a server
    serverObject = ServerWithAsyncio(hostname, port, log_file)
    # Start the server
    serverObject.main()
