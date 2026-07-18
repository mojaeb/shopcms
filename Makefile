.PHONY: install test test-cov migrate up down up-prod logs shell

install:
	pip install -r requirements/development.txt

test:
	pytest

test-cov:
	pytest --cov=. --cov-report=term-missing

migrate:
	python manage.py migrate

up:
	docker compose -f docker/docker-compose.yml up --build

down:
	docker compose -f docker/docker-compose.yml down

up-prod:
	docker compose -f docker/docker-compose.prod.yml up --build -d

logs:
	docker compose -f docker/docker-compose.prod.yml logs -f web

shell:
	python manage.py shell

seed:
	python manage.py seed_store
	python manage.py seed_roles
	python manage.py seed_plugins
