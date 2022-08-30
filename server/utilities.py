# Utilities file for server operations

import subprocess
from typing import List, Tuple, final


def execute_shell(cmd: str) -> str:
    grep = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True) # execute grep command using shell
    stdout, stderr = grep.communicate()
    if len(stderr) == 0:
        return stdout
    else:
        print(f"grep command {cmd} failed with error: {stderr}") # ! make the error more generic
        return b'failed to retrive logs'

def prepare_shell_cmd(query: str, logpath: str) -> Tuple[int, str]:
    query_prefix = "search "

    if not query.startswith(query_prefix):
        return (1, str.encode("invalid query: expected search ['<query string 1>', '<query string 2>']"))

    try:
        search_strings = ast.literal_eval(query[len(query_prefix):])
        cmd = "grep "
        for search_string in search_strings:
            cmd += f"-e '{search_string}' "
        cmd += logpath
        return (0, cmd)
    except:
        return (1, str.encode("invalid query: expected search ['<query string 1>', '<query string 2>']"))