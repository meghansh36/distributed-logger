from typing import List, Tuple, final
import ast
import sys
import getopt

MAX_QUERY_SIZE: final = 5120

'''
function to prepare grep commands to get matched line count and actual matched lines from log files
'''
def prepare_grep_shell_cmds(query: str, logpath: str) -> Tuple[int, List[bytes]]:

    query_prefix = "search "

    if not query.startswith(query_prefix):
        return (1, [str.encode("invalid query: expected search ['<query string 1>', '<query string 2>']")])

    try:
        search_strings = ast.literal_eval(query[len(query_prefix):])
        cmds = []

        # form query to get count of all the matched lines
        cmd = "grep -c "
        for search_string in search_strings:
            cmd += f"-e '{search_string}' "
        cmd += logpath
        cmds.append(cmd.encode())

        # form query to seach all the matched lines
        cmd = "grep "
        for search_string in search_strings:
            cmd += f"-e '{search_string}' "
        cmd += logpath
        cmds.append(cmd.encode())

        return (0, cmds)
    except:
        return (1, [str.encode("invalid query: expected search ['<query string 1>', '<query string 2>']")])


'''
parse cmdline options for server
'''
def parse_server_cmdline_args(arguments):
    
    hostname = '127.0.0.1'
    port = 8000
    log_file = 'logs/machine.log'

    try:
        opts, args = getopt.getopt(arguments, "h:p:l:", [
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
    
    return hostname, port, log_file
