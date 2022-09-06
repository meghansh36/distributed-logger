from socket import socket
import subprocess

'''
Execute provided command with shell and return the reponse.
'''
def execute_shell(cmd: str) -> bytes:
    # execute grep command using shell
    grep = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, shell=True)
    stdout, stderr = grep.communicate()
    if len(stderr) == 0:
        return stdout
    else:
        print(f"command {cmd} failed with error: {stderr}")
        return b'command failed'


'''
Send provided bytes using sock object
'''
def socket_send_bytes(sock: socket, data: bytes) -> None:
    try:
        sock.sendall(data)
    except:
        print('failed to send')
