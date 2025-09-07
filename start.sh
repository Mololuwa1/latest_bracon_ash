#!/bin/bash
echo "🌞 Starting Heliotelligence..."
docker-compose up -d
echo ""
echo "⏳ Waiting for services..."
sleep 10
echo ""
echo "🧪 Running tests..."
./test_docker.sh --quick
echo ""
echo "🎉 Ready! Open http://localhost"
