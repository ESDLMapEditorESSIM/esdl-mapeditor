all:
	docker-compose -f docker/docker-compose.dev.yml build

dev:
	docker-compose -f docker/docker-compose.dev.yml up

dev-local: mongo
	python app.py

mongo:
	docker-compose -f docker/docker-compose.dev.yml up -d mongo

docker-beta:
	./beta-docker-container-redeploy
