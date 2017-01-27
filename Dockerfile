FROM python:3.6-alpine

RUN apk add --no-cache libffi gcc musl-dev libffi-dev autoconf make automake libtool
RUN apk add --no-cache libusb-dev eudev-dev  eudev linux-headers jpeg-dev zlib-dev

RUN mkdir -p /usr/src/app && mkdir -p /var/local/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
ENV SECP_BUNDLED_EXPERIMENTAL=1
RUN pip install --no-cache-dir -r requirements.txt
COPY test.py test.py
RUN rm requirements.txt