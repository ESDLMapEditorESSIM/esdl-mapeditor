FROM python:3.7-slim

RUN apt-get -y update
RUN apt-get install -y gcc libpcre3 libpcre3-dev zlib1g zlib1g-dev libssl-dev
RUN pip3.7 install --upgrade pip

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
RUN pip3.7 install -r requirements.txt

COPY . /usr/src/app
RUN pip install -e src/
ENV PYTHONPATH=.:/usr/src/app

EXPOSE 8111

CMD python app.py
