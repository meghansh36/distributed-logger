# AwesomeLogRetreiver

AwesomeLogRetreiver is a client/server applications which can be used to query distributed log files on multiple machines. The applications provides grep like interface on files distributed on multiple machines.

## server application

This is a simple python application which will listen on a configured port for search queries from multiple clients and searches a single log file or multiple log files in a directory based on the user query.

### Requirements

1. `python` >= `3.7.X` is required to run server application.

### How To Use This

1. Navigate to `server` folder.
2. Run server application with port, hostname and logfile details. `python3 server.py --hostname=<hostname or ip> --port=<server port for listening> --logfile=<path to a log file or log directory>`.

```
$ python3 server.py
Got a connection from ('127.0.0.1', 52736)
Got query from ('127.0.0.1', 52736): b"search ['blockMap']"
sending 50977 bytes
closing client connection: ('127.0.0.1', 52736)
```

## client application

This is a simple python application which provides CLI interface to users to input search queries which will internally forwards requests to multiple machines and displays the search results from different machines as if the search is performed on files locally.

### Requirements

1. `python` >= `3.7.X` is required to run server application.

### How To Use This

1. Navigate to `client` folder.
2. Fill in all the servers information as `<hostname or ip>, <port>` in the `servers.conf` file in any directory.
3. Run client application `python3 client.py --config=<full path to config file>`.
4. choose option `1` to display configured servers loaded from config file.
5. choose option `2` to input search query in the following format `search ['<search string 1 or regex>', <search string 2 or regex>' ...]`.

```
$ python3 client.py
-------------------------------
1. Display current servers
2. Search logs
3. exit
choose one of the following options: 1
servers:
1: ('127.0.0.1', 8000)
-------------------------------
1. Display current servers
2. Search logs
3. exit
choose one of the following options: 2
Enter search query (Ex: 'search ['query1', 'query2]'): search ['blockMap']
fetching logs from all the servers ...
logs from server (127.0.0.1:8000):
logs/machine.log: 314
081109 204005 35 INFO dfs.FSNamesystem: BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.251.73.220:50010 is added to blk_7128370237687728475 size 67108864
081109 204132 26 INFO dfs.FSNamesystem: BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.251.43.115:50010 is added to blk_3050920587428079149 size 67108864
081109 204324 34 INFO dfs.FSNamesystem: BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.251.203.80:50010 is added to blk_7888946331804732825 size 67108864
...

matched line count per server: 
('127.0.0.1', 8000): 314
('127.0.0.1', 8001): 0
Total matched line count for all server: 314
-------------------------------
1. Display current servers
2. Search logs
3. exit
choose one of the following options: 3
```

## Testing

