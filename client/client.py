#!/opt/homebrew/bin/python3
import sys
import asyncio
import signal
import getopt
import time
from typing import List, Tuple


async def fetch_logs_from_server(server_hostname: str, server_port: int, query: str) -> Tuple[int, str]:

    try:
        reader, writer = await asyncio.open_connection(
            server_hostname, server_port
        )

        # print(
        #     f'sending query ({query}) to server: {server_hostname}:{server_port} ')
        writer.write(query.encode())
        await writer.drain()

        num_log_lines = 0
        logs = ""
        while True:

            log_line = await reader.readline()
            if not log_line:
                # print(
                #     f'server ({server_hostname}:{server_port}) connection closed')
                break

            log_line = log_line.decode()
            if log_line:
                logs += log_line
                num_log_lines += 1

        # print(f'closing server ({server_hostname}:{server_port}) connection')
        writer.close()
        await writer.wait_closed()

        return num_log_lines - 1, logs

    except Exception as e:
        print(f'logs from server ({server_hostname}:{server_port}):')
        print(
            f'Failed to fetch logs from server with Exception ({e})')
        return 0, ""


async def handle_user_query(server_details, query: str, print_logs_to_console: bool = True) -> None:

    background_tasks = []
    for hostname, port in server_details:
        background_tasks.append(fetch_logs_from_server(hostname, port, query))

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
    print(f"Total time taken to fetch all the logs from servers: {end - begin} seconds")


def fetch_server_details_from_config_file(filename: str) -> Tuple[Tuple[str, int]]:
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


def handler(signum, frame):
    sys.exit('Ctrl-c was pressed. Exiting the application')


if __name__ == "__main__":

    servers_config_file = 'servers.conf'
    logs_to_console = True

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

    except getopt.GetoptError:
        print("usage: python3 client.py --config='servers.conf' --logsToConsole=True/False")
        sys.exit(2)

    # read servers details from log_servers.conf file
    server_details = fetch_server_details_from_config_file(servers_config_file)

    # register for a signal handler to handle Ctrl + c
    signal.signal(signal.SIGINT, handler)

    while True:

        try:
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
                # schedule tasks in async io event loop
                asyncio.run(handle_user_query(server_details, query, logs_to_console))
            elif option == 3:
                sys.exit()
            else:
                print(f'invalid option {option}.')
        except Exception as e:
            print(f'invalid user input: {e}')
