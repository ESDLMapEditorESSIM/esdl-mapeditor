FROM python:3.7-alpine

RUN apk add --update --no-cache g++ gcc libxslt-dev linux-headers musl-dev pcre pcre-dev zlib zlib-dev openssl-dev mailcap libffi-dev libffi
RUN pip3.7 install --upgrade pip

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
RUN pip3.7 install -r requirements.txt

COPY . /usr/src/app
WORKDIR /usr/src/app

ENV PYTHONPATH=.:/usr/src/app

EXPOSE 8111

CMD python app.py
