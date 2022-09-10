#!/opt/homebrew/bin/python3
import sys
import asyncio
import signal
import getopt
import time
from typing import List, Tuple

class Client:

    def __init__(self):
        pass

    '''
    coroutine to asyncronously connect, send and recv responses from a single server

    @params server_hostname: Hostname of server as specified in the config file
    @params server_port: Port on which server application is running
    @params query: Search query entered by user
    '''
    async def fetch_logs_from_server(self, server_hostname: str, server_port: int, query: str) -> Tuple[int, str]:

        try:
            # Connect to the server
            reader, writer = await asyncio.open_connection(
                server_hostname, server_port
            )

            # Send search query to the server
            writer.write(query.encode())
            await writer.drain()

            num_log_lines = 0
            logs = ""

            while True:
                # Read server response line by line
                log_line = await reader.readline()
                if not log_line:
                    break

                log_line = log_line.decode()
                # increment macthed line count and append each log line to logs variable
                if log_line:
                    logs += log_line
                    num_log_lines += 1

            # Close connection with server
            writer.close()
            await writer.wait_closed()

            return num_log_lines - 1, logs

        except Exception as e:
            print(f'logs from server ({server_hostname}:{server_port}):')
            print(
                f'Failed to fetch logs from server with Exception ({e})')
            return 0, ""

    '''
    coroutine to asyncronously handle user query by sending and receiving data from multiple servers

    @params server_details: Details of all servers from the config file
    @params query: Search query entered by user
    @params print_logs_to_console: Flag to turn off/on log printing to console

    '''
    async def handle_user_query(self, server_details, query: str, print_logs_to_console: bool = True) -> None:

        # list to keep track of all server tasks
        background_tasks = []
        for hostname, port in server_details:
            background_tasks.append(self.fetch_logs_from_server(hostname, port, query))

        begin = time.time()
        results = await asyncio.gather(*background_tasks, return_exceptions=True)
        end = time.time()

        if print_logs_to_console:
            for i in range(len(background_tasks)):
                print(
                    f'logs from server ({server_details[i][0]}:{server_details[i][1]}):')
                print(f'{results[i][1]}')

        print('matched line count per server: ')
        total_matched_count = 0
        for i in range(len(background_tasks)):
            print(f'{server_details[i]}: {results[i][0]}')
            total_matched_count += results[i][0]

        print(f'Total matched line count for all server: {total_matched_count}')
        # total time taken
        print(
            f"Total time taken to fetch all the logs from servers: {end - begin} seconds")


'''
function to read servers information from the config file

@params filename: path to the config file
'''
def fetch_server_details_from_config_file(filename: str) -> List[Tuple[str, int]]:
    servers = []
    try:
        with open(filename) as f:
            for line in f:
                hostname, port = line.split(',')
                hostname = hostname.strip()
                port = port.strip()
                servers.append((hostname, int(port)))
    except Exception as e:
        print(f'failed to read server details from {filename}')
        return []

    return servers


'''
signal handler function to catch and process Ctrl-c
'''
def handler(signum, frame):
    sys.exit('Ctrl-c was pressed. Exiting the application')

"""
Function to process command line arguments
"""
def process_cmd_line_args():
    servers_config_file = 'servers.conf'
    # This flag sets whether the matched lines will be printed to console or not
    logs_to_console = True

    # process command line options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "c:h", [
                                   "config=", "logsToConsole="])

        for opt, arg in opts:
            if opt in ("-c", "--config"):
                servers_config_file = arg
            elif opt in ("--logsToConsole"):
                if arg == "True":
                    logs_to_console = True
                elif arg == "False":
                    logs_to_console = False
                else:
                    print(
                        "usage: python3 client.py --config='servers.conf' --logsToConsole=True/False")
                    sys.exit(2)
            elif opt in ("-h"):
                print(
                    "usage: python3 client.py --config='servers.conf' --logsToConsole=True/False")
                sys.exit()
        
        return [servers_config_file, logs_to_console]

    except getopt.GetoptError:
        print("usage: python3 client.py --config='servers.conf' --logsToConsole=True/False")
        sys.exit(2)


if __name__ == "__main__":

    # Fetch config file path and logs_to_console flag from command line arguments
    [servers_config_file, logs_to_console] = process_cmd_line_args()

    # read servers details from servers.conf file
    server_details = fetch_server_details_from_config_file(servers_config_file)

    # register for a signal handler to handle Ctrl + c
    signal.signal(signal.SIGINT, handler)

    while True:

        try:
            # Display menu options to the user
            print('-------------------------------')
            print("1. Display current servers")
            print("2. Search logs")
            print("3. exit")

            option = int(input("choose one of the following options: "))

            if option == 1:
                print("servers:")
                i = 0
                for server_detail in server_details:
                    print(f'{i + 1}: {server_details[i]}')
                    i += 1
            
            elif option == 2:
                query = str(
                    input("Enter search query (Ex: 'search ['query1', 'query2]'): "))
                print('fetching logs from all the servers ...')

                # schedule tasks in asyncio event loop
                client = Client()
                asyncio.run(client.handle_user_query(
                    server_details, query, logs_to_console))

            elif option == 3:
                sys.exit()
            else:
                print(f'invalid option {option}.')
        except Exception as e:
            print(f'invalid user input: {e}')
