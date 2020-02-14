#!/bin/bash

docker build -t mapeditor-beta:latest -f docker/Dockerfile-uwsgi .
docker stop mapeditor-beta
docker rm mapeditor-beta
docker run -d  --name mapeditor-beta --restart always -p 2503:8111 -e MAPEDITOR_HESI_ENERGY=1 mapeditor-beta:latest
