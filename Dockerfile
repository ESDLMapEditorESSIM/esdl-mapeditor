FROM ubuntu:latest
LABEL authors="lars"

ENTRYPOINT ["top", "-b"]