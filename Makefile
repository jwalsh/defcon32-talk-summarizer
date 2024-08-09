PYTHON=python3
PIP=pip3
DOCKER=docker
IMAGE_NAME=defcon32-summarizer
CONTAINER_NAME=defcon32-summarizer-container
MIRROR_DIR=defcon32-media

.PHONY: install run test clean build docker-build docker-test docker-run docker-mirror help mirror check-env
.DEFAULT_GOAL := help

# Help
help:
	@echo "Available targets:"
	@awk '/^[a-zA-Z\-\_0-9]+:/ { \
		helpMessage = match(lastLine, /^# (.*)/); \
		if (helpMessage) { \
			helpCommand = substr($$1, 0, index($$1, ":")-1); \
			helpMessage = substr(lastLine, RSTART + 2, RLENGTH); \
			printf "  %-20s %s\n", helpCommand, helpMessage; \
		} \
	} \
	{ lastLine = $$0 }' $(MAKEFILE_LIST)

# Install dependencies
install:
	$(PIP) install -r requirements.txt

# Mirror DEFCON 32 media
mirror:
	@echo "Mirroring DEFCON 32 media"
	@mkdir -p $(MIRROR_DIR)
	@./mirror_defcon.sh $(MIRROR_DIR)

# Run the program locally
run:
	@echo "Running the program locally"
	$(PYTHON) src/summarizer.py

# Run tests
test:
	$(PYTHON) -m unittest discover -v -s tests

# Clean up
clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	rm -rf .pytest_cache
	rm -rf build dist *.egg-info

build: install test

# Check if COHERE_API_KEY is set
check-env: 
ifndef COHERE_API_KEY
	$(error COHERE_API_KEY is undefined)
endif

# Docker targets
# Build the docker image
docker-build:
	$(DOCKER) build -t $(IMAGE_NAME) .

# Test the docker image
docker-test:
	$(DOCKER) run --rm --name $(CONTAINER_NAME) $(IMAGE_NAME)

# Run the program in a docker container
docker-run: check-env
	$(DOCKER) run -it --rm \
		--network host \
		-v $(PWD)/$(MIRROR_DIR):/home/appuser/$(MIRROR_DIR) \
		-v $(PWD)/summaries:/home/appuser/summaries \
		-e COHERE_API_KEY=$(COHERE_API_KEY) \
		$(IMAGE_NAME) python src/summarizer.py \
		--pdf-dir /home/appuser/$(MIRROR_DIR) \
		--output-dir /home/appuser/summaries

# Run the mirror script in a docker container
docker-mirror:
	$(DOCKER) run -it --rm \
		-v $(PWD)/$(MIRROR_DIR):/home/appuser/$(MIRROR_DIR) \
		$(IMAGE_NAME) ./mirror_defcon.sh /home/appuser/$(MIRROR_DIR)

all: clean docker-build docker-test
