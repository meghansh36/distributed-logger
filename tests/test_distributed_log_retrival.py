from http import client
import json
import os
import sys
from typing import List
sys.path.insert(0, os.getcwd() + '/../')
from client.client import Client
import asyncio
import signal

'''
parse the custom testcase format
'''
def parse_server_details(filename: str, test_name: str):
    servers = []
    pattern = ''
    expected_line_count_per_server = []
    try:
        with open(filename) as f:
            config = json.loads(f.read())
            test_details = config[test_name]
            pattern = test_details['pattern']
            for server in test_details['servers']:
                servers.append((server['hostname'], server['port']))
                expected_line_count_per_server.append(server['expected_line_count'])
    except Exception as e:
        print(f'failed to read server details from {filename}')
        return ([], '', 0)

    return servers, pattern, expected_line_count_per_server


'''
function to send queries to all the connected clients
'''
async def validate_user_query(server_details: List, query: str, expected_log_count_per_server: List) -> None:

    # create client object
    client = Client()

    background_tasks = []
    for hostname, port in server_details:
        background_tasks.append(client.fetch_logs_from_server(hostname, port, query))

    results = await asyncio.gather(*background_tasks, return_exceptions=True)

    for i in range(len(background_tasks)):
        actual_logs_count, _ = results[i]
        expected_logs_count = expected_log_count_per_server[i]
        print(f'validating server ({server_details[i][0]}:{server_details[i][1]}) logs:')
        if expected_logs_count == actual_logs_count:
            print(f'PASS')
        else:
            print(f'FAIL')
            print(f'actual log count: {actual_logs_count}, expected log count: {expected_logs_count}')


'''
function to execute and validate test cases
'''
def test_log_pattern(test_name: str):

    print(f'Testing log retriver for {test_name}.')

    server_details, pattern, expected_line_count_per_server = parse_server_details("config/test_servers_details.json", test_name)

    print(f'using following servers for testing: ')
    for hostname, port in server_details:
        print(f'{hostname}:{port}')
    
    query = "search ['" + pattern + "']"

    print(f'sending query ({query}) to all the configured servers.')
    # send query to all the servers and validate response
    asyncio.run(validate_user_query(server_details, query, expected_line_count_per_server))

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
            print("4. Run all tests.")
            print('5. Exit')

            option = int(input("choose one of the following options: "))

            if option == 1:
                test_log_pattern("infrequent_pattern")
            elif option == 2:
                test_log_pattern("frequent_pattern")
            elif option == 3:
                test_log_pattern("invalid_servers")
            elif option == 4:
                test_log_pattern("infrequent_pattern")
                test_log_pattern("frequent_pattern")
                test_log_pattern("invalid_servers")
            else:
                sys.exit()
        except Exception as e:
            print(f'invalid user input: {e}')
