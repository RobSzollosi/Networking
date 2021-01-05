CS3357 ASN4 - Web Load Balancer
Robert Szollosi 
250917994

To use the balancer as described in this assignment you will need 3 directories 
with the following files:

1. client_dir - client.py

2. balancer_dir - balancer.py, 301.html, 404.html, 501.html, 505.html, config.txt

3. server_dir - server.py, 404.html, 501.html, 505.html, testing.jpg, + other files 
that the client will request to download

server
------

To run the server, simply execute:

  python server.py

potentially substituting your installation of python3 in for python depending
on your distribution and configuration.  The server will report the port 
number that it is listening on for your client to use.  Place any files to 
transfer into the same directory as the server.

balancer
--------

To run the balancer, execute:

  python3 balancer.py config.txt

where config.txt is a file containing the host:port for each server that you want 
to have incduced in the web load balancing (each host:port should be on a new line).
I have included a sample config.txt that I used for testing, so you can just edit 
it as necessary.

client
------

To run the client, execute:

  python3 client.py http://host:port/file

where host is where the balancer is running (e.g. localhost), port is the port 
number reported by the balancer where it is running and file is the name of the 
file you want to retrieve.  Again, you might need to substitute python3 in for
python depending on your installation and configuration.

if you wish to bypass the balancer and simply connect to the server as in asn2, 
then simply substitute the balncer host:port for that of the server that you would
like to connect to instead.

