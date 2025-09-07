# 🌞 Heliotelligence Docker Setup

Complete Docker deployment for the Heliotelligence solar energy prediction platform.

## 🚀 Quick Start

```bash
# Clone or extract the project
cd heliotelligence_docker_corrected

# Build and start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

**Access the application**: http://localhost

## 📁 Project Structure

```
heliotelligence_docker_corrected/
├── backend/                    # FastAPI backend application
│   ├── main_monitoring.py     # Main application with monitoring
│   ├── models.py              # Pydantic data models
│   ├── weather.py             # Weather API integration
│   ├── database.py            # Database models and setup
│   └── monitoring.py          # Real-time monitoring system
├── core/                      # Physics engine
│   └── solar_farm_simulator.py
├── frontend/                  # React frontend application
│   ├── src/                   # Source code
│   ├── package.json           # Node.js dependencies
│   └── vite.config.js         # Build configuration
├── nginx/                     # Nginx configuration
│   └── nginx.conf             # Reverse proxy config
├── data/                      # Persistent data storage
├── logs/                      # Application logs
├── docker-compose.yml         # Multi-service orchestration
├── Dockerfile                 # Container definition
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🐳 Docker Services

### 1. heliotelligence-app
- **Technology**: FastAPI + React (built into static files)
- **Port**: 8000 (internal)
- **Features**: 
  - Physics-based solar predictions
  - Real-time monitoring
  - Weather data integration
  - Static file serving

### 2. nginx
- **Technology**: Nginx reverse proxy
- **Port**: 80 (external)
- **Features**:
  - Load balancing
  - Static file caching
  - Security headers
  - Rate limiting

## 🔧 Configuration

### Environment Variables

Create a `.env` file for custom configuration:

```env
# Application
ENVIRONMENT=production
PYTHONPATH=/app

# Database (optional - defaults to SQLite)
DATABASE_URL=sqlite:///./data/heliotelligence.db

# Weather API
PVGIS_API_URL=https://re.jrc.ec.europa.eu/api/tmy

# Monitoring
ENABLE_MONITORING=true
LOG_LEVEL=INFO
```

### Port Configuration

Default ports:
- **Frontend/API**: http://localhost (port 80)
- **Direct API**: http://localhost:8000 (development only)

To change ports, modify `docker-compose.yml`:

```yaml
services:
  nginx:
    ports:
      - "8080:80"  # Use port 8080 instead of 80
```

## 🧪 Testing

### Health Checks

```bash
# Application health
curl http://localhost/health

# API documentation
curl http://localhost/docs

# Frontend
curl http://localhost
```

### API Testing

```bash
# Test prediction endpoint
curl -X POST http://localhost/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "location": {"latitude": 51.5074, "longitude": -0.1278, "altitude": 11},
    "array": {"tilt": 35, "azimuth": 180, "stringing": {"modules_per_string": 20, "strings_per_inverter": 10}},
    "module_params": {"power": 400, "temp_coefficient": -0.35},
    "inverter_params": {"power": 50000, "efficiency": 96.5},
    "loss_params": {"soiling": 2.0, "shading": 1.0, "snow": 0.5, "mismatch": 2.0, "wiring": 2.0, "connections": 0.5, "lid": 1.5, "nameplate": 1.0, "age": 0.0, "availability": 3.0}
  }'
```

## 🛠️ Development

### Local Development

For development with hot reload:

```bash
# Start backend only
docker-compose up heliotelligence-app

# In another terminal, start frontend development server
cd frontend
npm install
npm run dev
```

### Building Images

```bash
# Build without cache
docker-compose build --no-cache

# Build specific service
docker-compose build heliotelligence-app
```

### Debugging

```bash
# View logs
docker-compose logs heliotelligence-app
docker-compose logs nginx

# Execute commands in container
docker-compose exec heliotelligence-app bash

# Check container resources
docker stats
```

## 📊 Monitoring

### Application Metrics

- **Health endpoint**: `/health`
- **Metrics endpoint**: `/api/v1/monitoring/metrics`
- **System status**: `/api/v1/monitoring/status`

### Container Monitoring

```bash
# Resource usage
docker stats

# Container health
docker-compose ps

# Logs with timestamps
docker-compose logs -t -f
```

## 🔒 Security

### Production Considerations

1. **Environment Variables**: Use secrets management
2. **SSL/TLS**: Configure HTTPS with certificates
3. **Firewall**: Restrict access to necessary ports
4. **Updates**: Regularly update base images

### Security Headers

Nginx is configured with security headers:
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin

## 🚀 Production Deployment

### SSL Configuration

Add SSL certificates to nginx:

```yaml
# docker-compose.prod.yml
services:
  nginx:
    volumes:
      - ./ssl:/etc/nginx/ssl:ro
      - ./nginx/nginx-ssl.conf:/etc/nginx/nginx.conf:ro
    ports:
      - "443:443"
      - "80:80"
```

### Scaling

Scale the application:

```bash
# Scale to multiple instances
docker-compose up -d --scale heliotelligence-app=3

# Use external load balancer
# Update nginx upstream configuration
```

### Backup

```bash
# Backup data volume
docker run --rm -v heliotelligence_app_data:/data -v $(pwd):/backup alpine tar czf /backup/data-backup.tar.gz /data

# Backup database
docker-compose exec heliotelligence-app python -c "
from backend.database import engine
import subprocess
subprocess.run(['sqlite3', '/app/data/heliotelligence.db', '.dump'], 
               stdout=open('/app/data/backup.sql', 'w'))
"
```

## 🐛 Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Find process using port 80
sudo lsof -i :80

# Stop conflicting services
sudo systemctl stop apache2  # or nginx
```

#### Container Won't Start
```bash
# Check logs
docker-compose logs heliotelligence-app

# Rebuild image
docker-compose build --no-cache heliotelligence-app
```

#### Frontend Not Loading
```bash
# Check if static files were built
docker-compose exec heliotelligence-app ls -la /app/static/

# Rebuild with frontend
docker-compose build --no-cache
```

#### API Requests Fail
```bash
# Check backend health
curl http://localhost:8000/health

# Check nginx configuration
docker-compose exec nginx nginx -t
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Increase memory limits in docker-compose.yml
services:
  heliotelligence-app:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

## 📈 Performance Optimization

### Caching

- Static files cached for 1 year
- API responses can be cached with Redis
- Database query optimization

### Resource Limits

Configure in `docker-compose.yml`:

```yaml
services:
  heliotelligence-app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

## 📞 Support

### Logs Location

- Application logs: `./logs/`
- Nginx logs: Inside nginx container at `/var/log/nginx/`
- Docker logs: `docker-compose logs`

### Health Checks

All services include health checks:
- Application: HTTP GET `/health`
- Nginx: HTTP GET `/health` (proxied)

### Useful Commands

```bash
# Full restart
docker-compose down && docker-compose up -d

# Update images
docker-compose pull && docker-compose up -d

# Clean up
docker system prune -a
```

## 🎯 Next Steps

1. **SSL Setup**: Configure HTTPS for production
2. **Monitoring**: Add Prometheus/Grafana
3. **CI/CD**: Automate deployments
4. **Scaling**: Configure load balancing
5. **Backup**: Implement automated backups

Your Heliotelligence platform is now running in Docker! 🌞

