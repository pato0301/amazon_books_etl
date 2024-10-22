# Makefile

# Variables
COMPOSE_FILE := docker-compose.yaml

.PHONY: run stop build test clean

# Start the services in detached mode
run:
	docker-compose -f $(COMPOSE_FILE) up -d

# Stop and remove containers, networks, and volumes
stop:
	docker-compose -f $(COMPOSE_FILE) down

# Build the Docker images
build:
	docker-compose -f $(COMPOSE_FILE) build

# Clean up unused Docker resources
clean:
	docker-compose -f $(COMPOSE_FILE) down --volumes --remove-orphans

# Help message
help:
	@echo "Makefile commands:"
	@echo "  make run         Start the services in detached mode"
	@echo "  make stop        Stop and remove the containers"
	@echo "  make build       Build the Docker images"
	@echo "  make clean       Clean up unused Docker resources"
