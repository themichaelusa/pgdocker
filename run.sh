#!/bin/bash

# Variables
ENV_PATH=".env"
DOCKER_IMAGE_NAME="pg-docker"
PG_DATA_DIR_LOCAL="./pgdata"
PG_DATA_DIR_DOCKER="/var/lib/postgresql/data"
PG_PORT="6432"
MEMORY_LIMIT="29G"  # Example: Limit to 2 GB of memory
CPU_LIMIT="8.0"    # Example: Limit to 1 CPU

# Make the .env file readable
chmod 644 .env

# Ensure Docker Buildkit is enabled
export DOCKER_BUILDKIT=1

# Check if a buildx builder instance already exists
BUILDER_EXISTS=$(docker buildx ls | grep -w "localbuilder")
if [ -z "$BUILDER_EXISTS" ]; then
    # No builder named "mybuilder" exists, create it
    docker buildx create --name localbuilder --use
else
    # A builder named "mybuilder" exists, just use it
    docker buildx use localbuilder
fi

# Detect the architecture of the current machine
ARCH=$(uname -m)

case "$ARCH" in
    "x86_64")
        # Architecture is x86_64
        echo "Detected x86_64 architecture. Building and running the container for x86_64."
        # Build and run the container for x86 architecture
        docker buildx build --platform linux/amd64 -t $DOCKER_IMAGE_NAME --load .
        docker run -d --env-file $ENV_PATH -v $PG_DATA_DIR_LOCAL:$PG_DATA_DIR_DOCKER -p $PG_PORT:$PG_PORT --memory $MEMORY_LIMIT --cpus $CPU_LIMIT $DOCKER_IMAGE_NAME
        ;;
    "arm64" | "aarch64")
        # Architecture is ARM64
        echo "Detected ARM64 architecture. Building and running the container for ARM64."
        # Build and run the container for ARM architecture
        docker buildx build --no-cache --platform linux/arm64 -t $DOCKER_IMAGE_NAME --load .
        docker run -d --env-file $ENV_PATH -v $PG_DATA_DIR_LOCAL:$PG_DATA_DIR_DOCKER -p $PG_PORT:$PG_PORT --memory $MEMORY_LIMIT --cpus $CPU_LIMIT $DOCKER_IMAGE_NAME
        ;;
    *)
        echo "Unsupported architecture: $ARCH"
        exit 1
        ;;
esac