FROM python:3.9-slim

RUN apt-get -y update
RUN apt-get install -y gcc libpcre3 libpcre3-dev zlib1g zlib1g-dev libssl-dev
RUN pip install --upgrade pip

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
RUN pip install -r requirements.txt

COPY . /usr/src/app
RUN pip install -e src/
ENV PYTHONPATH=.:/usr/src/app

EXPOSE 8111

CMD python app.py
