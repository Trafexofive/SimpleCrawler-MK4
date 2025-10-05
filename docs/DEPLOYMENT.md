# SimpleCrawler MK4 - Deployment Guide

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- 4GB+ RAM recommended
- 2GB+ disk space for containers

### One-Command Deployment
```bash
git clone https://github.com/Trafexofive/SimpleCrawler-MK4.git
cd SimpleCrawler-MK4
make quick-start
```

This will:
1. Build all Docker containers
2. Start PostgreSQL, Redis, API, Workers, and Nginx
3. Run health checks
4. Display service status

## 🏗️ Production Deployment

### Environment Setup
```bash
# Clone and setup
git clone https://github.com/Trafexofive/SimpleCrawler-MK4.git
cd SimpleCrawler-MK4

# Production deployment
make deploy
```

### Environment Variables
Create a `.env` file for production:
```bash
# Database
DATABASE_URL=postgresql://crawler:secure_password@postgres:5432/crawler_db
POSTGRES_PASSWORD=secure_password

# Redis
REDIS_URL=redis://redis:6379

# API
API_HOST=0.0.0.0
API_PORT=8000

# Security
SECRET_KEY=your-secret-key-here
```

### Production Docker Compose
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  api:
    build: ./services/api
    deploy:
      replicas: 3  # Scale API instances
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    volumes:
      - ./app:/app/crawler:ro
      - crawler_output:/app/output
    restart: always

  worker:
    build: ./services/worker
    deploy:
      replicas: 5  # Scale workers
    restart: always
```

## 🔧 Configuration Options

### Scaling Services
```bash
# Scale workers for high load
make scale-workers WORKERS=10

# Or via docker-compose
docker-compose up -d --scale worker=10
```

### Resource Limits
```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### Health Checks
All services include health checks:
```bash
# Check all services
make health

# Individual service health
curl http://localhost:8000/health
```

## 🌐 Reverse Proxy Setup

### Nginx Configuration
The included `nginx.conf` provides:
- Load balancing
- Rate limiting (10 req/s)
- Security headers
- File serving for downloads

### Custom Domains
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://api:8000;
        # ... proxy headers
    }
}
```

## 📊 Monitoring

### Service Logs
```bash
# All services
make logs

# Specific services
make api-logs
make worker-logs
make db-logs
```

### Metrics Endpoints
- **API Health**: `GET /health`
- **Statistics**: `GET /stats`
- **Swagger Docs**: `GET /docs`

### Log Aggregation
For production, consider:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Prometheus + Grafana
- Docker logging drivers

## 🔒 Security Considerations

### Network Security
- Services communicate via internal Docker network
- Only API and Nginx expose ports
- Database and Redis are internal-only

### API Security
- Rate limiting enabled (configurable)
- Input validation with Pydantic
- Security headers via Nginx
- CORS configuration available

### Data Security
- PostgreSQL with connection pooling
- Redis with append-only persistence
- Volume encryption recommended for production

## 📈 Performance Tuning

### Database Optimization
```yaml
postgres:
  command: postgres -c max_connections=200 -c shared_buffers=256MB
  environment:
    POSTGRES_SHARED_PRELOAD_LIBRARIES: pg_stat_statements
```

### Redis Optimization
```yaml
redis:
  command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

### API Performance
- Async I/O throughout
- Connection pooling
- Background job processing
- Caching with Redis

## 🚨 Troubleshooting

### Common Issues

**Services not starting:**
```bash
# Check Docker resources
docker system df

# Check service logs
make logs

# Restart services
make restart
```

**API not responding:**
```bash
# Check API logs
make api-logs

# Check health endpoint
curl http://localhost:8000/health

# Restart API service
make api-restart
```

**Database connection issues:**
```bash
# Check PostgreSQL status
make db-shell

# Reset database (WARNING: destroys data)
make db-reset
```

**Worker jobs not processing:**
```bash
# Check worker logs
make worker-logs

# Check Redis queue
make redis-shell
# > LLEN crawl_queue

# Restart workers
make worker-restart
```

### Service Dependencies
If services fail to start, check dependencies:
1. PostgreSQL must be healthy before API starts
2. Redis must be healthy before workers start
3. API must be running before Nginx starts

## 🔄 Updates and Maintenance

### Updating the Application
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
make clean
make quick-start
```

### Database Migrations
```bash
# Backup before updates
make backup

# Apply schema changes (if any)
# Custom migration scripts would go here
```

### Backup Procedures
```bash
# Database backup
make backup

# Volume backup
docker run --rm -v crawler_output:/data -v $(pwd)/backups:/backup alpine tar czf /backup/output-$(date +%Y%m%d).tar.gz /data
```

## 🌟 Advanced Deployment

### Kubernetes
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crawler-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: crawler-api
  template:
    spec:
      containers:
      - name: api
        image: your-registry/crawler-api:latest
        ports:
        - containerPort: 8000
```

### Cloud Deployment
- **AWS**: ECS, EKS, or EC2
- **GCP**: Cloud Run, GKE, or Compute Engine
- **Azure**: Container Instances, AKS, or VMs

### CI/CD Pipeline
```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Deploy to production
      run: |
        docker-compose -f docker-compose.prod.yml up -d
```

## 📞 Support

- **GitHub Issues**: Bug reports and feature requests
- **Documentation**: `/docs` directory
- **Health Checks**: Built-in monitoring endpoints
- **Logs**: Comprehensive service logging

The SimpleCrawler MK4 platform is designed for easy deployment and scaling from development to production environments.