# ESDL MapEditor

## Introduction

This repository contains code for a map-based ESDL editor. It allows loading, editing and saving ESDL EnergySystem files,
as well as integration with various external services (ESSIM, Energy Data Repository, BAG, ...).

The ESDL MapEditor is part of a bigger software stack. See [the Docker Toolsuite repository](https://github.com/ESDLMapEditorESSIM/docker-toolsuite) for more information.

For more documentation go [here](https://energytransition.gitbook.io/esdl/esdl-based-tools/mapeditor).

## Build local docker container image

If you've updated this code and want to test it locally with the rest of the stack:

1. Build your docker container image:

   ```shell script
   docker build -t esdl-mapeditor:latest -f docker/Dockerfile-uwsgi .
   ```

2. Go to the docker-toolsuite project, and change the docker-compose yaml file to link to the local container image:

   ```yaml
   ...
   services:
     mapeditor:
     container_name: esdl-mapeditor
     # image: esdlmapeditoressim/esdl-mapeditor:latest
     image: esdl-mapeditor:latest
     networks:
       - mapeditor-net
     ports:
       - "${MAPEDITOR_PORT:-8111}:8111"
     env_file:
       - mapeditor_open_source.env
   ...
   ```

3. Start the software stack in the docker-toolsuite project using `docker-compose up`.

## Local development

Perform the following steps to run the mapeditor directly on your own machine. Prerequisites are Python3 and pip. You also need to be running the Docker Toolsuite.

1. Clone this repository.

2. Install the dependencies: `pip install -r requirements.txt` (you probably want to do this from inside a virtual environment)

3. Copy the `.env.local-os` file to a file named `.env`

4. Run the application: `python app.py`

5. Open a browser and go to `http://localhost:8111`.

## Local development in Docker

It is also possible to develop on this project directly from Docker. For this, we've defined a `docker-compose.dev.yml` file.

Prerequisites are Docker and docker-compose. Also, the Docker toolsuite needs to be running.

1. Build the local Docker image: `docker-compose -f docker/docker-compose.dev.yml build`

2. Run the container: `docker-compose -f docker/docker-compose.dev.yml up`

Every change made to the code will automatically reload the application. The above commands can also be found in the `Makefile`, for convenience.

## License

The ESDL MapEditor is distributed under the [Apache 2.0 License](http://www.apache.org/licenses/LICENSE-2.0).
