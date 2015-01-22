# powermeter_hub_server
A small web sever for logging power usage data from the Efergy Engage Hub without internet/cloud access.

These devices are sold for ~$120 AUD and the hardware looks quite well built.
Sadly, the firmware transmits all your meter data to a server run by a third
party in the UK and all access to the data is via efergy's web portal, Android
or iPhone apps.

This project provides a simple HTTPS server that you can redirect your hub to
traffic to that will act like their cloud infrastructure and allow you to gather
the raw meter readings into an sqlite3 database where you are free to use the
data as you please (or use the device without an internet connection, etc).

Requirements
============

* Python2.6+
* PyOpenSSL

I'm also using linux on a Raspberry Pi for this and haven't tried on other
platforms. To direct the traffic to the SSL server, you'll need either to run
your own DNS server to resolve all \*.sensornet.info addresses to the local
machine or leave the DNS alone and use iptables to redirect traffic.

Installation
============
Under linux, something like this:

    $ sudo iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 443 -j REDIRECT --to-port 8080
    $ python ./hub_server.py


There is also a little viewer app you can run to see data but it's not exactly
scalable. Using this long term isn't really an option:

    $ python ./web_server.py

This will give you a webserver at http://localhost:8081/ that will render your
power usage with dygraph.
