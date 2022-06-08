all: requirements yarn
	docker-compose -f docker/docker-compose.yml build

pip-compile:
	pip-compile
	pip-compile requirements-uwsgi.in
requirements:
	pip install -r requirements.txt
requirements-uwsgi:
	pip install -r requirements-uwsgi.txt
yarn:
	yarn

dev:
	python app.py
watch: yarn
	yarn && yarn run watch

dev-local:
	cp .env.local-os .env
	python app.py

docker-build:
	docker-compose -f docker/docker-compose.yml build
docker-dev:
	docker-compose -f docker/docker-compose.yml up
docker-down:
	docker-compose -f docker/docker-compose.yml down
docker-watch:
	docker-compose -f docker/docker-compose.yml up vue-watch
docker-watch-daemon:
	docker-compose -f docker/docker-compose.yml up -d vue-watch
