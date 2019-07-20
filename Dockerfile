FROM python:3.6-slim

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

RUN apt-get clean \
    && apt-get -y update

RUN apt-get -y install nginx \
    && apt-get -y install python3-dev \
    && apt-get -y install build-essential

RUN pip install --upgrade pip
RUN pip install -r requirements.txt --src /usr/local/src

COPY . /usr/src/app

ENV PYTHONPATH=.:/usr/src/app
ENV MAPEDITOR-TNO 1

COPY nginx.conf /etc/nginx
RUN chmod +x ./start.sh
CMD ["./start.sh"]