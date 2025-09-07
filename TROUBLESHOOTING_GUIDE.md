# 🔧 Heliotelligence Docker Troubleshooting Guide

## 🚨 Issues Encountered & Solutions

### **Issue 1: npm run build fails**
```
failed to solve: process "/bin/sh -c npm run build" did not complete successfully: exit code 1
```

**Root Cause**: Complex frontend build process failing in Docker environment.

**✅ Solution**: Use backend-only Dockerfile with embedded frontend.

### **Issue 2: Docker Compose version warning**
```
WARN: the attribute `version` is obsolete, it will be ignored
```

**Root Cause**: Docker Compose version 3.8 specification is deprecated.

**✅ Solution**: Removed version specification from docker-compose.yml.

### **Issue 3: No containers running**
```
❌ No containers running
```

**Root Cause**: Build failures prevent containers from starting.

**✅ Solution**: Use simplified Docker setup.

## 🚀 **WORKING SOLUTIONS**

### **Solution 1: Simple Setup (Recommended)**

```bash
# Use the simple start script
./start-simple.sh

# Or manually:
docker-compose -f docker-compose.simple.yml up -d
```

**Access**: http://localhost:8000

**Benefits**:
- ✅ No complex frontend build
- ✅ Single container setup
- ✅ Embedded HTML frontend
- ✅ All features working

### **Solution 2: Backend-Only Dockerfile**

```bash
# Use the backend-only Dockerfile (already set as default)
docker-compose build
docker-compose up -d
```

**Benefits**:
- ✅ No npm build issues
- ✅ Self-contained frontend
- ✅ Production-ready

### **Solution 3: Direct Backend Access**

```bash
# Build just the backend
docker build -t heliotelligence-backend .

# Run directly
docker run -p 8000:8000 heliotelligence-backend
```

**Access**: http://localhost:8000

## 🧪 **Testing Your Setup**

### **Quick Test Commands**

```bash
# Test health endpoint
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# Test frontend
curl http://localhost:8000 | grep "Heliotelligence"
# Expected: HTML content with "Heliotelligence"

# Test API prediction
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "location": {"latitude": 51.5074, "longitude": -0.1278, "altitude": 11},
    "array": {"tilt": 35, "azimuth": 180, "stringing": {"modules_per_string": 20, "strings_per_inverter": 10}},
    "module_params": {"power": 400, "temp_coefficient": -0.35},
    "inverter_params": {"power": 50000, "efficiency": 96.5},
    "loss_params": {"soiling": 2.0, "shading": 1.0, "snow": 0.5, "mismatch": 2.0, "wiring": 2.0, "connections": 0.5, "lid": 1.5, "nameplate": 1.0, "age": 0.0, "availability": 3.0}
  }'
```

### **Expected Results**

```bash
$ docker-compose -f docker-compose.simple.yml ps
NAME                    COMMAND                  STATUS
heliotelligence-app     "uvicorn backend.mai…"   Up (healthy)

$ curl http://localhost:8000/health
{"status":"healthy","timestamp":"2025-08-25T02:00:00Z"}

$ curl -s http://localhost:8000 | grep -o "Heliotelligence"
Heliotelligence
```

## 🔧 **Available Docker Files**

### **1. Dockerfile (Default - Backend-Only)**
- ✅ **Recommended**: Works without frontend build
- ✅ **Features**: Embedded HTML frontend with full functionality
- ✅ **Access**: http://localhost:8000

### **2. Dockerfile.simple**
- ✅ **Alternative**: Single-stage build with Node.js
- ✅ **Use case**: If you want to modify frontend
- ⚠️ **Note**: May still have npm build issues

### **3. Dockerfile.original**
- ❌ **Problematic**: Multi-stage build with npm issues
- ❌ **Status**: Backup only, not recommended

### **4. Dockerfile.with-lock**
- ⚠️ **Advanced**: Multi-stage with package-lock.json
- ⚠️ **Use case**: If you have npm expertise

## 🐳 **Docker Compose Options**

### **1. docker-compose.simple.yml (Recommended)**
```bash
docker-compose -f docker-compose.simple.yml up -d
```
- ✅ Single service (backend only)
- ✅ Direct port access (8000)
- ✅ No nginx complexity

### **2. docker-compose.yml (Standard)**
```bash
docker-compose up -d
```
- ⚠️ Includes nginx reverse proxy
- ⚠️ More complex setup
- ⚠️ Access via port 80

## 🛠️ **Step-by-Step Troubleshooting**

### **Step 1: Clean Start**
```bash
# Stop everything
docker-compose down
docker-compose -f docker-compose.simple.yml down

# Clean Docker
docker system prune -f

# Remove old images
docker rmi $(docker images -q heliotelligence*)
```

### **Step 2: Use Simple Setup**
```bash
# Use the working solution
./start-simple.sh

# Or manually
docker-compose -f docker-compose.simple.yml build --no-cache
docker-compose -f docker-compose.simple.yml up -d
```

### **Step 3: Verify Working**
```bash
# Check container status
docker-compose -f docker-compose.simple.yml ps

# Check logs
docker-compose -f docker-compose.simple.yml logs

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000
```

## 🚨 **Common Issues & Fixes**

### **Issue**: Port 8000 already in use
```bash
# Find what's using the port
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different port
# Edit docker-compose.simple.yml: "8001:8000"
```

### **Issue**: Permission denied
```bash
# On Linux/Mac, you might need sudo
sudo docker-compose -f docker-compose.simple.yml up -d

# Or add user to docker group
sudo usermod -aG docker $USER
# Then logout and login again
```

### **Issue**: Build still fails
```bash
# Use pre-built image approach
docker pull python:3.11-slim
docker build -t heliotelligence-backend . --no-cache
docker run -p 8000:8000 heliotelligence-backend
```

### **Issue**: Frontend doesn't work
```bash
# Check if static files exist
docker-compose -f docker-compose.simple.yml exec heliotelligence-app ls -la /app/static/

# The embedded frontend should be there automatically
```

## 📊 **Success Indicators**

### **✅ Everything Working**
```bash
$ ./start-simple.sh
🌞 Starting Heliotelligence (Simple Mode)...
✅ Health check passed
✅ Frontend loads successfully
🎉 Setup complete!
📱 Access: http://localhost:8000

$ curl http://localhost:8000/health
{"status":"healthy"}

$ curl -s http://localhost:8000 | grep "Solar Energy"
Solar Energy Prediction Platform
```

### **✅ Container Status**
```bash
$ docker-compose -f docker-compose.simple.yml ps
NAME                    IMAGE     COMMAND                  STATUS
heliotelligence-app     ...       "uvicorn backend.mai…"   Up (healthy)
```

### **✅ Frontend Features**
- Interactive map with UK cities
- Solar system configuration form
- Real-time prediction API calls
- Results visualization with charts
- Responsive design

## 🎯 **Recommended Workflow**

1. **Extract Package**
   ```bash
   tar -xzf heliotelligence_docker_FIXED.tar.gz
   cd heliotelligence_docker_corrected
   ```

2. **Use Simple Setup**
   ```bash
   ./start-simple.sh
   ```

3. **Test Application**
   ```bash
   # Open browser to http://localhost:8000
   # Try generating a prediction
   # Check all features work
   ```

4. **If Issues Persist**
   ```bash
   # Check logs
   docker-compose -f docker-compose.simple.yml logs -f
   
   # Try manual build
   docker build -t test-heliotelligence .
   docker run -p 8000:8000 test-heliotelligence
   ```

## 📞 **Support Commands**

```bash
# View all available files
ls -la

# Check Docker status
docker info

# View container logs
docker-compose -f docker-compose.simple.yml logs -f

# Enter container for debugging
docker-compose -f docker-compose.simple.yml exec heliotelligence-app bash

# Test from inside container
docker-compose -f docker-compose.simple.yml exec heliotelligence-app curl http://localhost:8000/health
```

## 🎉 **Final Notes**

The **backend-only Dockerfile with embedded frontend** is the most reliable solution because:

- ✅ **No npm build complexity** - Frontend is embedded HTML
- ✅ **All features work** - Interactive maps, charts, API calls
- ✅ **Single container** - Simpler deployment
- ✅ **Production ready** - Includes health checks, logging
- ✅ **Easy to debug** - Clear error messages

Your Heliotelligence platform should now work perfectly! 🌞

