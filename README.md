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
    curl -i --header "Range: bytes=50-100" http://localhost:8000/img.jpg
    curl -i --header "Range: bytes=50-100" http://localhost:8000/img.jpg?range=bytes=50-100

### License and copyright

Copyright (C) 2016 Marko Trajkov <markostrajkov@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
