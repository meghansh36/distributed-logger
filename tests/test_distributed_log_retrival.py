import os
import sys
sys.path.insert(0, os.getcwd() + '/../')
from client import client
import time
import asyncio
import signal


def parse_server_details(filename: str):
    servers = []
    try:
        with open(filename) as f:
            for line in f:
                hostname, port, username, password = line.split(',')
                hostname = hostname.strip()
                port = port.strip()
                username = username.strip()
                password = password.strip()
                servers.append((hostname, int(port), username, password))
    except Exception as e:
        print(f'failed to read server details from {filename}')
        return []

    return servers


def start_server_applications(server_details):
    print(f'starting server applications')

def stop_server_applications(server_details):
    print(f'stopping server applications')


async def validate_user_query(server_details, query: str, expected_logs_per_server) -> None:

    background_tasks = []
    for hostname, port, _, _ in server_details:
        background_tasks.append(client.fetch_logs_from_server(hostname, port, query))

    results = await asyncio.gather(*background_tasks, return_exceptions=True)

    for i in range(len(background_tasks)):
        actual_logs_count, actual_logs = results[i]
        expected_logs_count, expected_logs = expected_logs_per_server[i]
        print(f'validating server ({server_details[i][0]}:{server_details[i][1]}) logs:')
        if (expected_logs_count == actual_logs_count) and (expected_logs == actual_logs):
            print(f'PASS')
        else:
            print(f'FAIL')
            print(f'actual log count: {actual_logs_count}, expected log count: {expected_logs_count}')
            print(f'actual logs:\n {actual_logs} \n expected logs:\n {expected_logs}')


def test_infrequent_log_pattern():

    print(f'Testing log retriver for infrequent log pattern.')

    server_details = parse_server_details("config/test_servers_details.conf")

    start_server_applications(server_details=server_details)

    time.sleep(10) # wait for servers to fully initialize

    query = "search ['subdir38']"

    expected_logs = ""
    with open('data/expected_infrequent_log_pattern_output.log') as f:
        expected_logs = f.read()

    expected_logs = [(8, expected_logs), (8, expected_logs)]

    print(f'sending query ({query}) to all the configured servers.')
    # send query to all the servers and validate response
    asyncio.run(validate_user_query(server_details, query, expected_logs))

    stop_server_applications(server_details=server_details)


def test_frequent_log_pattern():

    print(f'Testing log retriver for frequent log pattern.')

    server_details = parse_server_details("config/test_servers_details.conf")

    start_server_applications(server_details=server_details)

    query = "search ['a']"

    time.sleep(10) # wait for servers to fully initialize

    expected_logs = ""
    with open('data/expected_frequent_log_pattern_output.log') as f:
        expected_logs = f.read()

    expected_logs = [(2000, expected_logs), (2000, expected_logs)]

    print(f'sending query ({query}) to all the configured servers.')

    # send query to all the servers and validate response
    asyncio.run(validate_user_query(server_details, query, expected_logs))

    stop_server_applications(server_details=server_details)


def test_with_invalid_servers():

    print(f'Testing log retriver for invalid servers.')

    server_details = parse_server_details("config/test_invalid_servers_details.conf")

    query = "search ['subdir38']"

    expected_logs = [(0, ""), (0, "")]

    print(f'sending query ({query}) to all the configured servers.')

    # send query to all the servers and validate response
    asyncio.run(validate_user_query(server_details, query, expected_logs))


def handler(signum, frame):
    sys.exit('Ctrl-c was pressed. Exiting the application')


if __name__ == "__main__":

    while True:

        # register for a signal handler to handle Ctrl + c
        signal.signal(signal.SIGINT, handler)

        try:
            print('-------------------------------')
            print("1. Run infrequent pattern test.")
            print("2. Run frequent pattern test.")
            print("3. Run invalid server test.")
            print("4. Run All.")
            print('5. Exit')

            option = int(input("choose one of the following options: "))

            if option == 1:
                test_infrequent_log_pattern()
            elif option == 2:
                test_frequent_log_pattern()
            elif option == 3:
                test_with_invalid_servers()
            elif option == 4:
                test_infrequent_log_pattern()
                test_frequent_log_pattern()
                test_with_invalid_servers()
            else:
                sys.exit()
        except Exception as e:
            print(f'invalid user input: {e}')
