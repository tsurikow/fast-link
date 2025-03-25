#!/bin/bash

if [ ! -f ".env" ]; then
    echo ".env file not found. Using .env.dist as default."
    cp .env.dist .env
fi

docker-compose down

docker-compose up --build -d

echo "Deployment completed successfully!"