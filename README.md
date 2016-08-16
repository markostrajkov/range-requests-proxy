## Asynchronous HTTP proxy for HTTP/1.1 Range Requests

Built using Tornado (tested with version 4.4.1), supports HTTP GET method.

Can be used as standalone script, or integrated with your Tornado app.

If you need a loopback interface to test this proxy, please take a look at:
https://github.com/markostrajkov/range-requests-proxy-loopback


### Setup

    # install it
    python setup.py install

### Command-line usage

    python rangerequestsproxy/proxy.py 8000

### Unit Tests

    # run unit tests using setup.py
    python setup.py test

Or you can ran them directly: 'python -m unittest' or 'python -m pytest'
But you need to install following packages: ['pytest>=2.8.0', 'mock==2.0.0']

### Module usage

    from rangerequestsproxy.proxy import run_proxy

    run_proxy(8000)

### Usage with Docker

    # build the image
    docker build -t range-requests-proxy .

    # run the image
    docker run -t -p 127.0.0.1:8000:8000 --net="host" range-requests-proxy

### Usage with Docker Compose

    # build it
    docker-compose build

    # run it
    docker-compose up

### Manually testing the proxy

    You can use following curl commands to fire up a few curl request and test the proxy manually:

    # successful 206 requests
    curl -i --header "Range: bytes=0-50" http://localhost:8000/img.jpg
    curl -i --header "Range: bytes=0-" http://localhost:8000/img.jpg
    curl -i --header "Range: bytes=-50" http://localhost:8000/img.jpg
    curl -i --header "Range: bytes=0-50" http://localhost:8000/img.jpg?range=bytes=0-50

    # Requested range not satisfiable 416 requests
    curl -i --header "Range: bytes=0-50" http://localhost:8000/img.jpg?range=bytes=50-100
    curl -i --header "Range: bytes=a-50" http://localhost:8000/img.jpg

    # Stats:
    curl -i http://localhost:8000/stats
