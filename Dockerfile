FROM python:3.5

RUN mkdir -p /usr/local/range-requests-proxy

WORKDIR /usr/local/range-requests-proxy/

RUN mkdir -p rangerequestsproxy
RUN mkdir -p data

COPY requirements.txt setup.py start_all.sh loopback_server.py ./
COPY rangerequestsproxy/__init__.py rangerequestsproxy/proxy.py rangerequestsproxy/httprange.py rangerequestsproxy/
COPY data/img.jpg data/

ENV RANGE_REQUESTS_PROXY_ADDRESS http://127.0.0.1:9000,http://127.0.0.1:9000
ENV RANGE_REQUESTS_PROXY_DATA /usr/local/range-requests-proxy/data

RUN pip install -r requirements.txt
RUN python setup.py install

CMD bash start_all.sh
