#!/bin/bash
# =============================================================================
# Policy RAG - Docker Deployment Script (Linux/Mac)
# =============================================================================

set -e

echo ""
echo "======================================================================"
echo "  Policy RAG - Docker Deployment"
echo "======================================================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "[ERROR] Docker is not running. Please start Docker first."
    exit 1
fi

# Check if .env.docker exists
if [ ! -f ".env.docker" ]; then
    echo "[WARNING] .env.docker not found!"
    echo ""
    echo "Creating .env.docker from template..."
    cp ".env.docker.example" ".env.docker"
    echo ""
    echo "[ACTION REQUIRED] Please edit .env.docker and add your API keys:"
    echo "  - OPENAI_API_KEY"
    echo "  - PINECONE_API_KEY"
    echo "  - POSTGRES_PASSWORD (change the default!)"
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo "[INFO] Building and starting containers..."
echo ""

# Build and start containers
docker compose --env-file .env.docker up -d --build

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Docker deployment failed!"
    exit 1
fi

echo ""
echo "======================================================================"
echo "  Deployment Complete!"
echo "======================================================================"
echo ""
echo "  Frontend:  http://localhost"
echo "  Backend:   http://localhost:8001"
echo "  API Docs:  http://localhost:8001/docs"
echo "  Database:  PostgreSQL on localhost:5432"
echo ""
echo "  Useful commands:"
echo "    docker compose logs -f        # View logs"
echo "    docker compose down           # Stop all services"
echo "    docker compose ps             # Check status"
echo ""
echo "======================================================================"
echo ""
