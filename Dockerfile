FROM python:3.5

RUN mkdir -p /usr/local/range-requests-proxy

WORKDIR /usr/local/range-requests-proxy/

RUN mkdir -p rangerequestsproxy

COPY requirements.txt setup.py ./
COPY rangerequestsproxy/__init__.py rangerequestsproxy/proxy.py rangerequestsproxy/httprange.py rangerequestsproxy/

ENV RANGE_REQUESTS_PROXY_ADDRESS http://127.0.0.1:9000,http://127.0.0.1:9000

RUN pip install -r requirements.txt
RUN python setup.py install

CMD python /usr/local/range-requests-proxy/rangerequestsproxy/proxy.py
