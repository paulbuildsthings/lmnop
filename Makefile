# stop on error, no built in rules, run silently
MAKEFLAGS="-S -s -r"

IMAGE_ID := "ghcr.io/paullockaby/lmnop"

all: build

.PHONY: build
build:
	docker-compose build

.PHONY: up
up:
	docker-compose up

.PHONY: down
down:
	docker-compose down

.PHONY: pull
pull:
	docker-compose pull

.PHONY: push
push: build
	# get the version number from the portal container
	$(eval VERSION=$(shell docker run --rm ${IMAGE_ID}/portal --version | sed 's/+/-/'g))

	# tag the portal container
	docker tag $(IMAGE_ID)/portal:latest $(IMAGE_ID)/portal:$(VERSION)
	docker push $(IMAGE_ID)/portal:$(VERSION)

	# tag the builder container
	docker tag $(IMAGE_ID)/builder:latest $(IMAGE_ID)/builder:$(VERSION)
	docker push $(IMAGE_ID)/builder:$(VERSION)

	# tag the router container
	docker tag $(IMAGE_ID)/router:latest $(IMAGE_ID)/router:$(VERSION)
	docker push $(IMAGE_ID)/router:$(VERSION)

.PHONY: clean
clean:
	rm -rf dist/
	rm -rf .pytest_cache
	rm -rf builder/.pytest_cache
	rm -rf portal/.pytest_cache
	find . -type d -name "__pycache__" -print0 | xargs -0 rm -rf
	docker-compose rm -f
