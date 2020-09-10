# ESDL MapEditor

## Introduction

Map-based ESDL editor, allows loading, editing and saving ESDL EnergySystem files,
as well as integration with various external services (ESSIM, Energy Data
Repository, BAG, ...).

The ESDL MapEditor is part of a bigger software stack, see [here](https://github.com/ESDLMapEditorESSIM/docker-toolsuite) for more information.

For more documentation go [here](https://energytransition.gitbook.io/esdl/esdl-based-tools/mapeditor)

## Build local docker container image
If you've updated this code and want to test it locally with the rest of the stack:

1. Build your docker container image
   ```shell script
   docker build -t esdl-mapeditor:latest -f docker/Dockerfile-uwsgi .
   ```

2. Go to the docker-toolsuite project, change the docker-compose yaml file to link to the local container image
   ```yaml
   ...
   services:
     mapeditor:
     container_name: esdl-mapeditor
     esdlmapeditoressim/esdl-mapeditor:latest
     networks:
       - mapeditor-net
     ports:
       - "${MAPEDITOR_PORT:-8111}:8111"
     env_file:
       - mapeditor_open_source.env
   ...
   ```
 
3. Start the software stack using `docker-compose up -d`

## Local installation of this software
1. Clone this repository.

2. Install the dependencies: `pip install -r requirements.txt`

## Starting a local instance of the application (with the docker-toolsuite)
1. Copy the `.env.local-os` file to a file named `.env`

2. Run the application: `python app.py`

3. Open a browser and go to `http://localhost:8111`.

## License

The ESDL MapEditor is distributed under the [Apache 2.0 License](http://www.apache.org/licenses/LICENSE-2.0).