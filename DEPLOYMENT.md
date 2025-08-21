# Deployment Guide

This guide covers different ways to deploy the AI Craigslist Link Generator.

## 🚀 Local Development

### Quick Start
```bash
# Clone and setup
git clone <your-repo>
cd CraigsLink

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp env.example .env
# Edit .env and add your OpenAI API key

# Run the application
python app.py
```

### Using the Startup Script
```bash
# Make script executable (if not already)
chmod +x start.sh

# Run startup script
./start.sh
```

## 🌐 Production Deployment

### Option 1: Gunicorn + Nginx (Recommended)

#### 1. Install Gunicorn
```bash
pip install gunicorn
```

#### 2. Create Gunicorn Configuration
Create `gunicorn.conf.py`:
```python
bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 50
preload_app = True
```

#### 3. Create Systemd Service
Create `/etc/systemd/system/craigslist-bot.service`:
```ini
[Unit]
Description=AI Craigslist Link Generator
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/path/to/your/app
Environment=PATH=/path/to/your/venv/bin
ExecStart=/path/to/your/venv/bin/gunicorn -c gunicorn.conf.py app:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

#### 4. Start the Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable craigslist-bot
sudo systemctl start craigslist-bot
sudo systemctl status craigslist-bot
```

#### 5. Nginx Configuration
Create `/etc/nginx/sites-available/craigslist-bot`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/craigslist-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Option 2: Docker Deployment

#### 1. Create Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Run the application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

#### 2. Build and Run
```bash
# Build the image
docker build -t craigslist-bot .

# Run the container
docker run -d \
    --name craigslist-bot \
    -p 5000:5000 \
    --env-file .env \
    craigslist-bot

# Check logs
docker logs craigslist-bot

# Stop the container
docker stop craigslist-bot
```

#### 3. Docker Compose (Recommended for Docker)
Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  craigslist-bot:
    build: .
    ports:
      - "5000:5000"
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - craigslist-bot
    restart: unless-stopped
```

Run with:
```bash
docker-compose up -d
```

### Option 3: Cloud Deployment

#### Heroku
```bash
# Install Heroku CLI
# Create Procfile
echo "web: gunicorn app:app" > Procfile

# Deploy
heroku create your-app-name
heroku config:set OPENAI_API_KEY=your_key_here
git push heroku main
```

#### Railway
```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy
railway login
railway init
railway up
```

#### Render
```bash
# Connect your GitHub repo
# Set environment variables in dashboard
# Deploy automatically on push
```

## 🔒 Security Considerations

### Environment Variables
- Never commit `.env` files
- Use secure secret management in production
- Rotate API keys regularly

### Rate Limiting
Consider implementing rate limiting:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/generate-link', methods=['POST'])
@limiter.limit("10 per minute")
def generate_link():
    # Your existing code
```

### HTTPS
- Always use HTTPS in production
- Set up SSL certificates (Let's Encrypt)
- Redirect HTTP to HTTPS

## 📊 Monitoring

### Health Checks
The app includes a health endpoint:
```bash
curl http://your-domain.com/api/health
```

### Logging
Configure logging in production:
```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/craigslist-bot.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Craigslist Bot startup')
```

### Performance Monitoring
Consider adding:
- Application Performance Monitoring (APM)
- Error tracking (Sentry)
- Uptime monitoring (UptimeRobot)

## 🔧 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Find process using port 5000
   lsof -i :5000
   # Kill the process
   kill -9 <PID>
   ```

2. **Permission Issues**
   ```bash
   # Fix file permissions
   chmod +x start.sh
   chmod 644 .env
   ```

3. **OpenAI API Issues**
   - Check API key validity
   - Verify account has credits and access to GPT-5 nano (lowest cost model)
   - Check rate limits

4. **Memory Issues**
   - Reduce number of Gunicorn workers
   - Monitor memory usage
   - Consider container limits

## 📈 Scaling

### Horizontal Scaling
- Use load balancer (HAProxy, Nginx)
- Multiple application instances
- Database connection pooling

### Vertical Scaling
- Increase server resources
- Optimize Python code
- Use async workers (Gevent)

### Caching
Consider adding Redis for:
- API response caching
- Rate limiting
- Session storage

---

For more help, check the main README.md or open an issue on the repository.
