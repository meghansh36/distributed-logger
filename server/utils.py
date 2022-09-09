from socket import socket
import subprocess
from time import sleep, time


class Utils(object):

    '''
    Execute provided command with shell and return the reponse.
    '''
    @staticmethod
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
    @staticmethod
    def socket_send_bytes(sock: socket, data: bytes) -> None:
        
            bytes_written = 0
            while bytes_written < len(data):
                try:
                    bytes_written += sock.send(data[bytes_written:])
                    print(f'written {bytes_written} bytes')
                except Exception as e:
                    print(f'failed to send {e}')
                    sleep(0.1)
