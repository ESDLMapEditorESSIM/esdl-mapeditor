#!/bin/bash

# Make sure to first push the right version to the dice branch, and wait for the CI build to finish.

docker pull ci.tno.nl/geis/esdl-mapeditor/esdl-mapeditor:dice
docker tag ci.tno.nl/geis/esdl-mapeditor/esdl-mapeditor:dice tnonl/esdl-mapeditor-dice-beta:latest
docker push tnonl/esdl-mapeditor-dice-beta:latest
