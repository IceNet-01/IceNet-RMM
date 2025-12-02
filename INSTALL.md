# IceNet RMM Installation Guide

## Quick Start with Docker (Recommended)

### Prerequisites
- Docker and Docker Compose installed
- 4GB RAM minimum (8GB+ recommended for production)
- Valid SSL certificate (for production)

### Installation Steps

1. **Clone the repository:**
```bash
git clone https://github.com/your-org/icenet-rmm.git
cd icenet-rmm
```

2. **Configure environment:**
```bash
cp .env.example .env
nano .env  # Edit with your settings
```

3. **Start services:**
```bash
docker-compose up -d
```

4. **Create superuser:**
```bash
docker-compose exec backend python manage.py createsuperuser
```

5. **Access the control panel:**
- Web UI: https://your-domain.com
- API Docs: https://your-domain.com/api/docs/
- Admin: https://your-domain.com/admin/

## Manual Installation

### Backend (Django)

1. **Install Python 3.11+:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip postgresql redis-server
```

2. **Setup PostgreSQL:**
```bash
sudo -u postgres createdb icenet_rmm
sudo -u postgres createuser icenet_user
sudo -u postgres psql
postgres=# ALTER USER icenet_user WITH PASSWORD 'your_password';
postgres=# GRANT ALL PRIVILEGES ON DATABASE icenet_rmm TO icenet_user;
```

3. **Install backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
```

4. **Run backend:**
```bash
# Development
python manage.py runserver

# Production (with Daphne)
daphne -b 0.0.0.0 -p 8000 core.asgi:application
```

5. **Start Celery workers:**
```bash
celery -A core worker -l info
celery -A core beat -l info
```

### Frontend (Vue.js)

1. **Install Node.js 20+:**
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

2. **Install frontend:**
```bash
cd frontend
npm install
```

3. **Run frontend:**
```bash
# Development
npm run dev

# Production build
npm run build
```

### Agent (Go)

1. **Install Go 1.21+:**
```bash
wget https://go.dev/dl/go1.21.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.21.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bin
```

2. **Build agent:**
```bash
cd agent
go mod download
go build -o icenet-agent ./cmd/main.go
```

3. **Install agent on endpoint:**

**Windows:**
```powershell
.\icenet-agent.exe install --server https://your-rmm-server.com --token YOUR_TOKEN
```

**Linux:**
```bash
sudo ./icenet-agent install --server https://your-rmm-server.com --token YOUR_TOKEN
```

## NATS Installation

```bash
# Download and install NATS server
wget https://github.com/nats-io/nats-server/releases/download/v2.10.7/nats-server-v2.10.7-linux-amd64.tar.gz
tar -xzf nats-server-v2.10.7-linux-amd64.tar.gz
sudo cp nats-server-v2.10.7-linux-amd64/nats-server /usr/local/bin/

# Run NATS
nats-server -js -m 8222
```

## Production Deployment

### Using Systemd (Linux)

1. **Backend service:**
```bash
sudo nano /etc/systemd/system/icenet-backend.service
```

```ini
[Unit]
Description=IceNet RMM Backend
After=network.target postgresql.service

[Service]
Type=simple
User=icenet
WorkingDirectory=/opt/icenet/backend
Environment="PATH=/opt/icenet/backend/venv/bin"
ExecStart=/opt/icenet/backend/venv/bin/daphne -b 0.0.0.0 -p 8000 core.asgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

2. **Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable icenet-backend
sudo systemctl start icenet-backend
```

### Nginx Configuration

```nginx
upstream django_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://django_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws/ {
        proxy_pass http://django_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /static/ {
        alias /opt/icenet/backend/staticfiles/;
    }

    location /media/ {
        alias /opt/icenet/backend/media/;
    }
}
```

## Troubleshooting

### Database connection issues:
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connection
psql -U icenet_user -d icenet_rmm -h localhost
```

### Redis connection issues:
```bash
# Check Redis status
sudo systemctl status redis

# Test connection
redis-cli ping
```

### NATS connection issues:
```bash
# Check NATS status
curl http://localhost:8222/varz

# View NATS logs
journalctl -u nats-server -f
```

### Agent installation issues:
```bash
# Check agent logs (Linux)
journalctl -u icenet-agent -f

# Check agent logs (Windows)
# Event Viewer > Application and Services Logs
```

## Security Considerations

1. **Change default passwords** in .env file
2. **Use strong SECRET_KEY** for Django
3. **Enable HTTPS** with valid SSL certificates
4. **Configure firewall** to restrict access
5. **Enable MFA** for all users
6. **Regular backups** of database
7. **Keep software updated**

## Next Steps

1. Configure your first organization
2. Generate agent registration tokens
3. Deploy agents to endpoints
4. Set up update policies
5. Configure alerting

For more information, see the [User Guide](docs/USER_GUIDE.md).
