all:
	docker-compose -f docker/docker-compose.dev.yml build

dev:
	docker-compose -f docker/docker-compose.dev.yml up

requirements:
	pip install -r requirements.txt

dev-local:
	cp .env.local-os .env
	python app.py
