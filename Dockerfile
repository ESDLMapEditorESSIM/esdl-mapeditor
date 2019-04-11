FROM python:3-alpine
MAINTAINER Edwin Matthijssen  <edwin.matthijssen@tno.nl>

RUN apk add --update --no-cache g++ gcc libxslt-dev

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY Shapely-1.6.4.post1-cp37-cp37m-win_amd64.whl /usr/src/app
RUN pip install Shapely-1.6.4.post1-cp37-cp37m-win_amd64.whl

COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

ENV PYTHONPATH=.:/usr/src/app

EXPOSE 5000

CMD cd /usr/src/app && python app.py