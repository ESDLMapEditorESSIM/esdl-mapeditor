# ESDL MapEditor

## Introduction

This repository contains code for a map-based ESDL editor. It allows loading, editing and saving ESDL EnergySystem files,
as well as integration with various external services (ESSIM, Energy Data Repository, BAG, ...).

The ESDL MapEditor is part of a bigger software stack. See [the Docker Toolsuite repository](https://github.com/ESDLMapEditorESSIM/docker-toolsuite) for more information.

For more documentation go [here](https://energytransition.gitbook.io/esdl/esdl-based-tools/mapeditor).

The MapEditor integrates with several models and tools of external partners:
- The Energy Transition Model (ETM) of Quintel
- The VESTA model of PBL / ObjectVision
- The PICO model of Geodan
- The WANDA model of Deltares

## Current status and activities

The first prototype of the ESDL MapEditor was created in June 2019. Its first purpose was to serve as a frontend to
ESSIM, our ESDL based Energy System Simulator. The MapEditor appeared to provide the required visual representation of
an energy system by combining its technical, spatial, temporal and financial data. Since then the MapEditor was
used as a research prototype in different projects and extended based on various use cases. Nowadays, this is still
the case.

From within many different projects we're improving the ESDL MapEditor. Current activities involve:
- Introduction of a generic simulation framework - to connect and control external simulation engines 
- Introduction of functionality to perform sensitivity analyses 
- Better support for different control strategies (a.o. PID controllers)
- Improvement of the workflow engine
- Introduction of GEOS as GIS engine in the backend (GEOS is the engine that is used in PostGIS)
- Spatial optimization algorithms
- Introduction of a proper frontend framework
- Cleaning up the code and creating documentation

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

## Starting a local instance of the application (with the docker-toolsuite)

Perform the following steps to run the mapeditor directly on your own machine. Prerequisites are Python3 and pip. You also need to be running the Docker Toolsuite.

1. Clone this repository.

2. Install the dependencies: `pip install -r requirements.txt` (you probably want to do this from inside a virtual environment)

3. Copy the `.env.local-os` file to a file named `.env`

4. Install all vue dependencies: `yarn`

5. Build the vue part: `yarn watch`

6. Run the application: `python app.py`

7. Open a browser and go to `http://localhost:8111`.

## Local development in Docker

It is also possible to develop on this project directly from Docker. For this, we've defined a `docker-compose.dev.yml` file.

Prerequisites are Docker and docker-compose. Also, the Docker toolsuite needs to be running.

1. Build the local Docker image: `docker-compose -f docker/docker-compose.dev.yml build`

2. Run the container: `docker-compose -f docker/docker-compose.dev.yml up`

Every change made to the code will automatically reload the application. The above commands can also be found in the `Makefile`, for convenience.

## License

The ESDL MapEditor is distributed under the [Apache 2.0 License](http://www.apache.org/licenses/LICENSE-2.0).
