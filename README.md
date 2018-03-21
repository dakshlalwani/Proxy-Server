# Computer Networks Assignment-2
# Proxy Server with Cache
# Daksh Lalwani(20161156)

## Run commands
1. Extract and open the directory.
2. execute commands: 'python server.py' and 'python proxy.py'
3. Test the cache by the following command `curl -x http://localhost:12345 http://localhost:20000/<file_name>`

* We get message when a file enters, is already present, or update and stores in cache.
* we have taken a limit of storing at max of 3 files in the cache.

