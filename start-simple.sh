#!/bin/bash
echo "🌞 Starting Heliotelligence (Simple Mode)..."
echo "============================================"
echo ""

# Use the simple docker-compose file
docker-compose -f docker-compose.simple.yml up -d

echo ""
echo "⏳ Waiting for service to start..."
sleep 15

echo ""
echo "🧪 Testing the application..."

# Test health endpoint
echo "Testing health endpoint..."
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
fi

# Test frontend
echo "Testing frontend..."
if curl -s http://localhost:8000 | grep -q "Heliotelligence"; then
    echo "✅ Frontend loads successfully"
else
    echo "❌ Frontend failed to load"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📱 Access your application:"
echo "   🌐 Frontend: http://localhost:8000"
echo "   🔧 API Health: http://localhost:8000/health"
echo "   📚 API Docs: http://localhost:8000/docs"
echo ""
echo "🛠️ Useful commands:"
echo "   📊 View status: docker-compose -f docker-compose.simple.yml ps"
echo "   📋 View logs: docker-compose -f docker-compose.simple.yml logs -f"
echo "   🔄 Restart: docker-compose -f docker-compose.simple.yml restart"
echo "   🛑 Stop: docker-compose -f docker-compose.simple.yml down"
echo ""

