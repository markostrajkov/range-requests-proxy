#!/bin/bash

# start callback server in background, (un)comment following line if you (do not) need callback server
python /usr/local/range-requests-proxy/loopback_server.py &

#start proxy server
python /usr/local/range-requests-proxy/rangerequestsproxy/proxy.py
