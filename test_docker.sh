#!/bin/bash
# Heliotelligence Docker Test Script

echo "🌞 Heliotelligence Docker Test"
echo "============================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test functions
test_docker() {
    echo -e "${BLUE}🐳 Testing Docker...${NC}"
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}❌ Docker is not running${NC}"
        return 1
    fi
    echo -e "${GREEN}✅ Docker is running${NC}"
    return 0
}

test_containers() {
    echo -e "${BLUE}📦 Checking containers...${NC}"
    if ! docker-compose ps | grep -q "Up"; then
        echo -e "${RED}❌ No containers running${NC}"
        echo "Run: docker-compose up -d"
        return 1
    fi
    echo -e "${GREEN}✅ Containers are running${NC}"
    docker-compose ps
    return 0
}

test_health() {
    echo -e "${BLUE}🏥 Testing health endpoint...${NC}"
    sleep 5  # Wait for services to start
    
    response=$(curl -s -w "%{http_code}" http://localhost/health -o /tmp/health.json)
    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✅ Health check passed${NC}"
        cat /tmp/health.json | jq . 2>/dev/null || cat /tmp/health.json
        rm -f /tmp/health.json
        return 0
    else
        echo -e "${RED}❌ Health check failed (HTTP $response)${NC}"
        return 1
    fi
}

test_frontend() {
    echo -e "${BLUE}🌐 Testing frontend...${NC}"
    response=$(curl -s -w "%{http_code}" http://localhost -o /tmp/frontend.html)
    if [ "$response" = "200" ] && grep -q "Heliotelligence" /tmp/frontend.html; then
        echo -e "${GREEN}✅ Frontend loads successfully${NC}"
        rm -f /tmp/frontend.html
        return 0
    else
        echo -e "${RED}❌ Frontend failed (HTTP $response)${NC}"
        rm -f /tmp/frontend.html
        return 1
    fi
}

test_api() {
    echo -e "${BLUE}⚡ Testing prediction API...${NC}"
    response=$(curl -s -w "%{http_code}" -X POST http://localhost/api/v1/predict \
        -H "Content-Type: application/json" \
        -d '{
            "location": {"latitude": 51.5074, "longitude": -0.1278, "altitude": 11},
            "array": {"tilt": 35, "azimuth": 180, "stringing": {"modules_per_string": 20, "strings_per_inverter": 10}},
            "module_params": {"power": 400, "temp_coefficient": -0.35},
            "inverter_params": {"power": 50000, "efficiency": 96.5},
            "loss_params": {"soiling": 2.0, "shading": 1.0, "snow": 0.5, "mismatch": 2.0, "wiring": 2.0, "connections": 0.5, "lid": 1.5, "nameplate": 1.0, "age": 0.0, "availability": 3.0}
        }' -o /tmp/prediction.json)
    
    if [ "$response" = "200" ] && grep -q "annual_energy_kwh" /tmp/prediction.json; then
        echo -e "${GREEN}✅ Prediction API works${NC}"
        echo "Sample result:"
        cat /tmp/prediction.json | jq '.annual_energy_kwh, .performance_ratio' 2>/dev/null || echo "Prediction generated"
        rm -f /tmp/prediction.json
        return 0
    else
        echo -e "${RED}❌ Prediction API failed (HTTP $response)${NC}"
        rm -f /tmp/prediction.json
        return 1
    fi
}

# Main execution
main() {
    total_tests=5
    passed_tests=0
    
    test_docker && ((passed_tests++))
    echo ""
    
    test_containers && ((passed_tests++))
    echo ""
    
    test_health && ((passed_tests++))
    echo ""
    
    test_frontend && ((passed_tests++))
    echo ""
    
    test_api && ((passed_tests++))
    echo ""
    
    # Summary
    echo -e "${BLUE}📊 Test Summary${NC}"
    echo "==============="
    
    if [ $total_tests -eq $passed_tests ]; then
        echo -e "${GREEN}🎉 All tests passed! ($passed_tests/$total_tests)${NC}"
        echo ""
        echo -e "${GREEN}✅ Heliotelligence is ready!${NC}"
        echo ""
        echo "🌐 Access: http://localhost"
        echo "📚 API Docs: http://localhost/docs"
        echo "🔍 Health: http://localhost/health"
    else
        echo -e "${RED}❌ Some tests failed ($passed_tests/$total_tests)${NC}"
        echo ""
        echo "🔧 Try:"
        echo "  docker-compose logs"
        echo "  docker-compose restart"
        echo "  docker-compose down && docker-compose up -d"
    fi
}

# Help
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Heliotelligence Docker Test Script"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --help, -h    Show this help"
    echo "  --quick, -q   Quick tests only"
    echo ""
    echo "Tests Docker setup and application functionality"
    exit 0
fi

# Quick mode
if [ "$1" = "--quick" ] || [ "$1" = "-q" ]; then
    echo "🚀 Quick Test Mode"
    echo ""
    test_docker && echo -e "${GREEN}✅ Docker OK${NC}" || echo -e "${RED}❌ Docker Failed${NC}"
    test_containers && echo -e "${GREEN}✅ Containers OK${NC}" || echo -e "${RED}❌ Containers Failed${NC}"
    test_health && echo -e "${GREEN}✅ Health OK${NC}" || echo -e "${RED}❌ Health Failed${NC}"
    echo ""
    echo "🌐 Open http://localhost"
    exit 0
fi

# Run all tests
main

