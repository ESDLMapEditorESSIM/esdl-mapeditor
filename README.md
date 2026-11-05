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

   ```shell
   docker build -t esdl-mapeditor:latest -f docker/Dockerfile .
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

### Prerequisites

Python 3.13 is used for local development and the Docker images.

Make sure that pip is installed. We use pip-tools to manage our dependencies. For just running the mapeditor it is not
required to install it, but if you want to update dependencies, you do need it. You can install it through pip, using
`pip install pip-tools`. If in a terminal, you might need to close it and start it again for the commands to work.

The frontend code is written in JavaScript, using the Vue framework. Please make sure you have an up to date version of
NodeJS installed (please refer to the `Dockerfile`).

We use Yarn Modern to manage our JavaScript dependencies. Yarn Modern is **not** installable through npm but is
distributed through `Corepack`. It is not required for you to install as the binary is included in the project in the
.yarn folder. But you do need to enable Corepack by running `corepack enable` in your terminal.

You also need to be running the Docker Toolsuite.

### Installation

Perform the following steps to run the mapeditor directly on your own machine.

1. Clone this repository.

2. Install the dependencies: `pip install -r requirements.txt` (you probably want to do this from inside a virtual environment)

3. Copy the `.env.local-os` file to a file named `.env`

4. Install all vue dependencies: `yarn`

5. Run the Vue code compiler in dev mode: `yarn dev` (note that hot reloading only works for the Vue code)

6. Run the application: `python app.py`

7. Open a browser and go to `http://localhost:8111`.

### Legacy yarn watch fallback

If you can't use vite, replace step 5 with `yarn watch` and make sure the FRONTEND_DEV_URL is not set in the mapeditor.

If you get an 'ERR_OSSL_EVP_UNSUPPORTED' error, set the NODE_OPTIONS environment variable to '--openssl-legacy-provider' (without the quotes).

## Local development in Docker

It is also possible to develop on this project directly from Docker. For this, we've defined a `docker-compose.yml` file.

Prerequisites are Docker and docker-compose. Also, the Docker toolsuite needs to be running.

1. Copy the proper env file to .env, for example `cp .env.open-source .env`

2. Build the local Docker image: `docker-compose -f docker/docker-compose.yml build`

3. Run the container: `docker-compose -f docker/docker-compose.yml up`.

Every change made to the code will automatically reload the application, both the Python as well as the Vue part. The above commands can also be found in the `Makefile`, for convenience.

## Releasing versions

For a new release or deployment, commit all your changes and then use `npm version patch` to update patch 
version `z` in version `x.y.z` (e.g. `21.4.1`). `x` is the year,
`y` is the month and `z` is the patch number in that month, according to our current versioning scheme.
Use `npm version minor` to update `y` version value (i.e. the month).  

This command will update the version in package.json and git tag the current release with the new version 
number and commit these changes in your local repository. Do a manual `git push && git push --tags` to send
this to the remote repository.

## Coding guidelines

### Python

We follow PEP8 coding guidelines. Use `flake8` to check your code.

All Python code is found under src and extensions, except for the app.py in the root. This app.py is the entry point for
the application. It is a Flask application, and it serves the frontend code.

The app.py file is too big. We are working on splitting it up into smaller files. For this, we introduced the concept
of extensions, which are classes that can be registered with the Flask application. The extensions are located in the
`extensions` directory. The extensions are registered in the `app.py` file. They contain one or more request handlers.

### JavaScript

We use eslint and jshint to check our JavaScript code. Make sure to install the eslint and jshint plugins in your IDE
and configure them to use the `.eslintrc` and `.jshintrc` files in the project root.

Casing is camelCase for variables and functions, PascalCase for classes and constructors, and UPPER_CASE for constants.

### Vue

We use the Vue framework for the frontend. We use the Vue CLI to build the frontend code. The Vue code is located in the
`vue` directory. The entry point is `vue/index.js`. The Vue components are located in the `vue/components` directory.

There is no Vue router. The applicaiton was initially built with plain JavaScript, and Vue was added later. The Vue
files are now built like a library, and we mount Vue applications through plain JavaScript code.
## Environment variables

| Name                          | Description                                                                         | Used by                     | Default value if not specified | 
|-------------------------------|-------------------------------------------------------------------------------------|-----------------------------|--------------------------------|
| FLASK_DEBUG                   |                                                                                     |                             | ""                             |
| ALLOWED_ORIGINS               |                                                                                     |                             | *                              |
| OIDC_CLIENT_SECRETS           |                                                                                     |                             | None                           |
| MAPEDITOR_USE_GEVENT          |                                                                                     |                             | ""                             |
| POSTGRES_HOST                 | Postgres host                                                                       | DataManager                 | localhost                      |
| POSTGRES_PORT                 | Postgres port                                                                       | DataManager                 | 5432                           |
| POSTGRES_USER                 | Postgres user                                                                       | DataManager                 | mapeditor                      |
| POSTGRES_PASSWORD             | Postgres password                                                                   | DataManager                 | password                       |
| POSTGRES_DB                   | Postgres database name                                                              | DataManager                 | mapeditor                      |
| SETTINGS_STORAGE_HOST         |                                                                                     |                             | None                           | 
| SETTINGS_STORAGE_PORT         |                                                                                     |                             | 27017                          |
| USER_LOGGING_HOST             |                                                                                     |                             | None                           |
| USER_LOGGING_PORT             |                                                                                     |                             | 8086                           |
| BOUNDARY_SERVICE_HOST         |                                                                                     |                             | None                           |
| BOUNDARY_SERVICE_PORT         |                                                                                     |                             | None                           |
| PROFILE_DATABASE_HOST         |                                                                                     |                             | None                           |
| PROFILE_DATABASE_PORT         |                                                                                     |                             | 8086                           |
| PANEL_SERVICE_EXTERNAL_URL    |                                                                                     |                             | None                           |
| PANEL_SERVICE_INTERNAL_URL    |                                                                                     |                             | None                           |
| PANEL_SERVICE_PROFILE_DB_HOST |                                                                                     |                             | None                           |
| PANEL_SERVICE_PROFILE_DB_PORT |                                                                                     |                             | 8086                           |
| ESSIM_URL                     | endpoint of the ESSIM instance                                                      | ESSIM interface             | None                           | 
| ESSIM_LOADFLOW_URL            | alternative endpoint of the ESSIM instance with loadflow software connected         | ESSIM interface             | None                           |
| ESSIM_INFLUX_URL              | directly communicated to ESSIM, used to create the datasource in Grafana            | ESSIM interface             | None                           |
| ESSIM_MAPEDITOR_INFLUX_URL    |                                                                                     | PD Toolsuite workflow       | ESSIM_INFLUX_URL               |
| ESSIM_GRAFANA_URL             | not used at the moment, used to be part of http body to ESSIM                       |                             | None                           |
| ESSIM_DATABASE_HOST           | used for downloading ESSIM results from the MapEditor, used for load duration curve | ESSIM interface, ESSIM_KPIs | None                           |
| ESSIM_DATABASE_PORT           | used for downloading ESSIM results from the MapEditor, used for load duration curve | ESSIM interface, ESSIM_KPIs | 8086                           | 
| EDR_URL                       |                                                                                     |                             | None                           |
| ESDL_DRIVE_URL                |                                                                                     |                             | None                           |
| IBIS_SERVICE_HOST             |                                                                                     |                             | None                           |
| BAG_SERVICE_HOST              |                                                                                     |                             | None                           |
| STATISTICS_SERVICE_HOST       |                                                                                     |                             | None                           |
| DISPATCHER_HOST               |                                                                                     |                             | http://localhost               |
| DISPATCHER_PORT               |                                                                                     |                             | 9200                           |
| USER_FEEDBACK_URL             |                                                                                     |                             | None                           |
|                               |                                                                                     |                             |                                |




## License

The ESDL MapEditor is distributed under the [Apache 2.0 License](http://www.apache.org/licenses/LICENSE-2.0).
