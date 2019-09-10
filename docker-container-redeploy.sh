#!/bin/bash

docker build -t mapeditor-public:latest -f docker/Dockerfile-uwsgi .
docker stop mapeditor-public
docker rm mapeditor-public
docker run -d  --name mapeditor-public --restart always -p 2502:8111 -e MAPEDITOR_HESI_ENERGY=1 mapeditor-public:latest
