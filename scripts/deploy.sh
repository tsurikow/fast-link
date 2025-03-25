#!/bin/bash

# Ensure .env file exists
if [ ! -f ".env" ]; then
    echo ".env file not found. Using .env.dist as default."
    cp .env.dist .env
fi

# Stop running containers (if any)
docker-compose down

# Build and start the project
docker-compose up --build -d

echo "Deployment completed successfully!"