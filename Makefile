# stop on error, no built in rules, run silently
MAKEFLAGS="-S -s -r"

all: build

.PHONY: build
build:
	docker-compose build

.PHONY: up
up:
	docker-compose up

.PHONY: pull
pull:
	docker-compose pull

.PHONY: down
down:
	docker-compose down

.PHONY: clean
clean:
	rm -rf dist/
	rm -rf .pytest_cache
	find . -type d -name "__pycache__" -print0 | xargs -0 rm -rf
