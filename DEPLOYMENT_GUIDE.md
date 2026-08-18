# Security MVP - Docker Deployment Guide

Complete guide for deploying the Security MVP platform on various cloud providers and servers.

---

## 📋 Prerequisites

- Docker & Docker Compose installed
- Git for cloning repository
- Domain name (for production)
- SSL certificates (for production)
- Email account for notifications (optional)

---

## 🚀 Quick Start (5 minutes)

### Local Development

```bash
# 1. Clone repository
git clone https://github.com/your-repo/pharmacy-security-mvp.git
cd pharmacy-security-mvp

# 2. Setup environment
cp .env.example .env
# Edit .env with your settings
nano .env

# 3. Start all services
docker-compose up -d

# 4. Initialize database
docker-compose exec db psql -U security_mvp -d security_mvp < security-mvp-schema.sql

# 5. View logs
docker-compose logs -f

# 6. Access services
# Frontend: http://localhost:3000
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Database: localhost:5432
```

---

## ☁️ Cloud Deployment

### Option 1: AWS (Recommended)

#### Using Docker on EC2

```bash
# 1. Launch EC2 instance
# - AMI: Ubuntu 22.04 LTS
# - Instance type: t3.medium (at least)
# - Security group: Allow 80, 443, 22
# - Storage: 50GB EBS volume

# 2. SSH into instance
ssh -i your-key.pem ubuntu@your-instance-ip

# 3. Install Docker
sudo apt-get update
sudo apt-get install -y docker.io docker-compose git
sudo usermod -aG docker ubuntu

# 4. Clone and setup
git clone https://github.com/your-repo/pharmacy-security-mvp.git
cd pharmacy-security-mvp
cp .env.example .env

# 5. Update environment for production
nano .env
# Set:
# - DOMAIN_NAME=your-domain.com
# - SECRET_KEY=generate-with: python -c "import secrets; print(secrets.token_urlsafe(32))"
# - DATABASE_URL to RDS endpoint (optional - for managed database)

# 6. Generate SSL certificates
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot certonly --standalone -d your-domain.com

# 7. Create SSL directory and copy certificates
mkdir -p ssl
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/key.pem
sudo chown $USER:$USER ssl/*

# 8. Start services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 9. Verify
curl https://your-domain.com/health
```

#### Using AWS ECS (Container Service)

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name pharmacy-security-mvp

# Push Docker images to ECR
aws ecr create-repository --repository-name pharmacy-security-api
aws ecr create-repository --repository-name pharmacy-security-dashboard

docker build -t pharmacy-security-api -f Dockerfile.backend .
docker build -t pharmacy-security-dashboard -f Dockerfile.frontend .

aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com

docker tag pharmacy-security-api:latest \
  123456789.dkr.ecr.us-east-1.amazonaws.com/pharmacy-security-api:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/pharmacy-security-api:latest

# Create RDS database
aws rds create-db-instance \
  --db-instance-identifier pharmacy-security-mvp \
  --db-instance-class db.t3.small \
  --engine postgres \
  --master-username security_mvp \
  --master-user-password <strong-password>

# Use ECS task definitions for deployment
# See: AWS CloudFormation or Terraform templates
```

---

### Option 2: Digital Ocean (Most Affordable)

```bash
# 1. Create Droplet
# - Ubuntu 22.04 LTS
# - 2GB RAM, 50GB SSD
# - Region: Nearest to customers

# 2. SSH into droplet
ssh root@droplet-ip

# 3. Initial setup
apt-get update && apt-get upgrade -y
apt-get install -y docker.io docker-compose git curl wget

# 4. Clone repository
cd /opt
git clone https://github.com/your-repo/pharmacy-security-mvp.git
cd pharmacy-security-mvp
cp .env.example .env

# 5. Setup SSL with Let's Encrypt
apt-get install -y certbot
certbot certonly --standalone -d your-domain.com

mkdir -p ssl
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/cert.pem
cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/key.pem

# 6. Update environment
nano .env

# 7. Start services
docker-compose up -d

# 8. Setup automatic certificate renewal
echo "0 0 * * * certbot renew --quiet" | crontab -
```

---

### Option 3: Heroku (Quickest for Testing)

```bash
# 1. Install Heroku CLI
curl https://cli.heroku.com/install.sh | sh

# 2. Login
heroku login

# 3. Create app
heroku create pharmacy-security-mvp

# 4. Add Postgres add-on
heroku addons:create heroku-postgresql:standard-0

# 5. Set environment variables
heroku config:set SECRET_KEY=your-secret-key
heroku config:set ENVIRONMENT=production

# 6. Deploy
git push heroku main

# 7. Run migrations
heroku run "python -c \"from main import Base; Base.metadata.create_all()\""

# 8. Open app
heroku open
```

---

### Option 4: Render.com (Easiest, GitHub-connected)

```bash
# 1. Create Render account (render.com)

# 2. Create PostgreSQL database
# - Dashboard → Databases → New Database
# - Name: security_mvp
# - Region: Closest to customers

# 3. Create Backend Service
# - Dashboard → Services → New Web Service
# - Select GitHub repository
# - Build command: pip install -r requirements.txt
# - Start command: python -m uvicorn main:app --host 0.0.0.0 --port 8000
# - Environment variables:
#   - DATABASE_URL: (copy from database dashboard)
#   - SECRET_KEY: (generate)
#   - ENVIRONMENT: production

# 4. Create Frontend Service
# - Dashboard → Services → New Static Site
# - Select GitHub repository
# - Build command: npm run build
# - Publish directory: build

# 5. Update frontend .env to point to backend
# REACT_APP_API_URL=https://your-backend.onrender.com
```

---

## 🔐 Production Hardening

### 1. Database Backups

```bash
# Automated daily backups
docker-compose exec db pg_dump -U security_mvp security_mvp | \
  gzip > /backups/security_mvp_$(date +%Y%m%d).sql.gz

# Add to crontab
0 2 * * * docker-compose exec db pg_dump -U security_mvp security_mvp | \
  gzip > /backups/security_mvp_$(date +\%Y\%m\%d).sql.gz
```

### 2. SSL Certificate Auto-Renewal

```bash
# Create renewal script
cat > /opt/renew-ssl.sh << 'EOF'
#!/bin/bash
cd /opt/pharmacy-security-mvp
certbot renew
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/cert.pem
cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/key.pem
docker-compose restart nginx
EOF

# Add to crontab
0 0 * * * /opt/renew-ssl.sh
```

### 3. Monitoring & Health Checks

```bash
# Monitor logs
docker-compose logs -f backend frontend

# Check service health
docker-compose exec backend curl http://localhost:8000/health
docker-compose exec frontend curl http://localhost:3000

# Monitor disk usage
df -h /

# Monitor Docker resources
docker stats
```

### 4. Security Best Practices

```bash
# 1. Set restrictive file permissions
chmod 600 .env
chmod 700 ssl/

# 2. Rotate SECRET_KEY periodically
# Generate new key and update .env
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 3. Regular security updates
sudo apt-get update && sudo apt-get upgrade -y

# 4. Firewall configuration (UFW)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# 5. Fail2ban for brute force protection
sudo apt-get install -y fail2ban
sudo systemctl enable fail2ban
```

---

## 📊 Scaling

### Horizontal Scaling (Multiple Backend Instances)

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend-1:
    build:
      context: .
      dockerfile: Dockerfile.backend
    environment:
      DATABASE_URL: postgresql://...
      SECRET_KEY: ...
    ports:
      - "8001:8000"

  backend-2:
    build:
      context: .
      dockerfile: Dockerfile.backend
    environment:
      DATABASE_URL: postgresql://...
      SECRET_KEY: ...
    ports:
      - "8002:8000"

  # Load balancer (nginx) distributes between backend-1 and backend-2
  nginx:
    upstream backend {
      least_conn;
      server backend-1:8000;
      server backend-2:8000;
      server backend-3:8000;
    }
```

### Vertical Scaling (Larger Instances)

```bash
# Monitor resource usage
docker stats --no-stream

# Increase Docker resource limits
docker update --memory 4g --memory-swap 4g backend

# Increase PostgreSQL max_connections
# Edit docker-compose.yml:
# POSTGRES_INITDB_ARGS: -c max_connections=500
```

---

## 🔍 Troubleshooting

### Port Already in Use

```bash
# Find process using port
lsof -i :3000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
docker-compose -p myapp up -d
```

### Database Connection Errors

```bash
# Check if database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Verify connection string
docker-compose exec backend python -c \
  "from sqlalchemy import create_engine; \
   engine = create_engine(os.getenv('DATABASE_URL')); \
   engine.execute('SELECT 1')"
```

### Memory Issues

```bash
# Clean up Docker images and containers
docker system prune -a

# Check disk space
df -h

# Limit container memory
docker-compose down
# Edit docker-compose.yml add:
# services:
#   backend:
#     deploy:
#       resources:
#         limits:
#           memory: 2G
docker-compose up -d
```

### Slow API Responses

```bash
# Check backend logs
docker-compose logs backend

# Monitor database queries
docker-compose exec db psql -c "SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Check connection pool
docker-compose exec backend python -c "from main import engine; print(engine.pool.checkedout())"
```

---

## 📈 Performance Tuning

### PostgreSQL

```sql
-- Increase connection limit
ALTER SYSTEM SET max_connections = 500;

-- Increase shared buffers (25% of RAM)
ALTER SYSTEM SET shared_buffers = '256MB';

-- Increase work memory
ALTER SYSTEM SET work_mem = '16MB';

-- Increase maintenance work memory
ALTER SYSTEM SET maintenance_work_mem = '256MB';

-- Reload config
SELECT pg_reload_conf();
```

### FastAPI

```python
# Increase workers in gunicorn
# docker-compose.yml:
command: gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### React

```bash
# Enable compression
# nginx.conf already has gzip enabled

# Optimize build
npm run build -- --analyze
```

---

## 🔄 CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build images
        run: |
          docker build -t pharmacy-security-api -f Dockerfile.backend .
          docker build -t pharmacy-security-dashboard -f Dockerfile.frontend .
      
      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker tag pharmacy-security-api myrepo/pharmacy-security-api:latest
          docker push myrepo/pharmacy-security-api:latest
      
      - name: Deploy to server
        run: |
          ssh -i ${{ secrets.SSH_KEY }} user@server.com << 'EOF'
          cd /opt/pharmacy-security-mvp
          docker-compose pull
          docker-compose up -d
          EOF
```

---

## 📞 Support

For issues:
1. Check logs: `docker-compose logs -f`
2. Verify services: `docker-compose ps`
3. Test API: `curl http://localhost:8000/health`
4. Check resource limits: `docker stats`

---

## ✅ Deployment Checklist

- [ ] Environment variables configured (.env)
- [ ] SSL certificates installed and valid
- [ ] Database backups configured
- [ ] Monitoring setup (logs, metrics)
- [ ] Firewall rules configured
- [ ] Auto-scaling configured (if needed)
- [ ] Alerting configured
- [ ] CI/CD pipeline working
- [ ] Health checks passing
- [ ] Load testing completed
- [ ] Performance acceptable (<200ms response time)
- [ ] Security audit passed
- [ ] Documentation updated
- [ ] Customer support trained

---

**Status**: ✅ Ready for production deployment
