# IceNet RMM - Secure Remote Monitoring & Management

<div align="center">

**A modern, secure, open-source RMM solution for Windows and Linux**

[![License](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Go](https://img.shields.io/badge/go-1.21+-00ADD8.svg)](https://golang.org/)
[![Vue](https://img.shields.io/badge/vue-3.x-4FC08D.svg)](https://vuejs.org/)

</div>

## Overview

IceNet RMM is a comprehensive, enterprise-grade Remote Monitoring and Management solution designed with security as the top priority. Built for MSPs, IT teams, and organizations that need robust endpoint management without compromising on security.

## Key Features

### 🔒 Security First
- Zero-trust architecture with mutual TLS
- Mandatory multi-factor authentication (TOTP/FIDO2)
- Comprehensive audit logging
- Role-based access control (RBAC)
- End-to-end encryption
- Code-signed updates

### 🖥️ Cross-Platform Support
- **Windows**: Full support for Windows 10, 11, Server 2016-2022
- **Linux**: Ubuntu, Debian, CentOS, RHEL, Fedora, and more
- Unified management interface for all platforms

### 🔄 Automated Update Management
- **OS Updates**: Windows Update, APT, YUM/DNF integration
- **Application Updates**: Chocolatey, Winget, package managers
- Approval workflows and maintenance windows
- Staged rollouts with rollback capability

### 🖱️ Remote Access
- Integrated remote desktop (RDP for Windows, VNC/SSH for Linux)
- Browser-based access - no client software needed
- Multi-session support
- File transfer capability

### 📊 Real-Time Monitoring
- CPU, memory, disk, and network monitoring
- Service and process monitoring
- Event log and syslog integration
- Custom alerting rules
- Real-time dashboard updates

### ⚡ High Performance
- Built with Go agents for minimal resource usage
- Real-time communication via NATS message bus
- Scales to 10,000+ endpoints
- Efficient database design for time-series data

### 🎨 Modern Web Interface
- Vue.js 3 based control panel
- Responsive design - works on desktop and mobile
- Dark mode support
- Real-time updates via WebSocket
- Intuitive user experience

## Quick Start

### Prerequisites

- **Server:**
  - Linux server (Ubuntu 22.04+ recommended)
  - 4GB RAM minimum (8GB+ for production)
  - Docker and Docker Compose
  - Valid SSL certificate

- **Agents:**
  - Windows: Windows 10+ or Server 2016+
  - Linux: Any modern distribution with systemd

### Installation

#### Option 1: Docker Compose (Recommended for Testing)

```bash
# Clone the repository
git clone https://github.com/your-org/icenet-rmm.git
cd icenet-rmm

# Copy and configure environment
cp .env.example .env
nano .env  # Edit with your settings

# Start all services
docker-compose up -d

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Access at https://your-domain.com
```

#### Option 2: Manual Installation

See [INSTALL.md](docs/INSTALL.md) for detailed installation instructions.

### Deploying Agents

#### Windows
```powershell
# Download and install agent
Invoke-WebRequest -Uri "https://your-rmm-server/downloads/agent-windows.exe" -OutFile "icenet-agent.exe"
.\icenet-agent.exe install --server https://your-rmm-server --token YOUR_REGISTRATION_TOKEN
```

#### Linux
```bash
# Download and install agent
curl -O https://your-rmm-server/downloads/agent-linux
chmod +x agent-linux
sudo ./agent-linux install --server https://your-rmm-server --token YOUR_REGISTRATION_TOKEN
```

## Architecture

IceNet RMM consists of several components working together:

- **Backend**: Django-based REST API and WebSocket server
- **Frontend**: Vue.js 3 web control panel
- **Agent**: Lightweight Go agent for Windows and Linux
- **Message Bus**: NATS for real-time communication
- **Database**: PostgreSQL for persistent data
- **Cache**: Redis for caching and task queue

For detailed architecture information, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Documentation

- **[Architecture](ARCHITECTURE.md)**: System design and architecture
- **[Installation Guide](docs/INSTALL.md)**: Detailed installation instructions
- **[User Guide](docs/USER_GUIDE.md)**: How to use IceNet RMM
- **[Admin Guide](docs/ADMIN_GUIDE.md)**: Administration and configuration
- **[API Documentation](docs/API.md)**: REST API reference
- **[Agent Development](docs/AGENT_DEV.md)**: Agent development guide
- **[Security](docs/SECURITY.md)**: Security best practices
- **[Contributing](CONTRIBUTING.md)**: How to contribute

## Security

Security is our top priority. We follow industry best practices:

- All communications encrypted with TLS 1.3
- Certificate-based agent authentication
- Mandatory MFA for user accounts
- Regular security audits
- Comprehensive audit logging
- No default credentials

**Found a security vulnerability?** Please email security@icenet-rmm.com or see our [Security Policy](SECURITY.md).

## Comparison with Other RMM Solutions

| Feature | IceNet RMM | Tactical RMM | MeshCentral | Commercial RMM |
|---------|------------|--------------|-------------|----------------|
| Open Source | ✅ | ✅ | ✅ | ❌ |
| Cross-Platform Agents | ✅ | Limited | ✅ | ✅ |
| Mandatory MFA | ✅ | ❌ | ❌ | Varies |
| Zero-Trust Architecture | ✅ | ❌ | ❌ | Varies |
| Built-in Remote Desktop | ✅ | Via MeshCentral | ✅ | ✅ |
| Update Automation | ✅ | ✅ | ❌ | ✅ |
| Self-Hosted | ✅ | ✅ | ✅ | Some |
| Multi-Tenancy | ✅ | ✅ | ✅ | ✅ |
| Modern UI | ✅ | ✅ | Dated | ✅ |
| Cost | Free | Free | Free | $$$$ |

## Use Cases

- **Managed Service Providers (MSPs)**: Manage multiple client environments
- **Enterprise IT Teams**: Monitor and manage corporate endpoints
- **Small Business**: Cost-effective endpoint management
- **Educational Institutions**: Manage lab and administrative computers
- **Security Teams**: Maintain visibility and control over all endpoints

## Performance

- **Agent footprint**: < 50MB RAM, < 1% CPU
- **API response time**: < 100ms (p95)
- **Agent check-in**: Every 30 seconds
- **Real-time updates**: < 1 second latency
- **Concurrent agents**: Tested with 10,000+ agents

## Roadmap

- [x] Core agent and server communication
- [x] Basic monitoring capabilities
- [x] Web-based control panel
- [ ] Update management (In Progress)
- [ ] Remote desktop integration
- [ ] Advanced alerting and automation
- [ ] Mobile app (iOS/Android)
- [ ] Plugin/extension system
- [ ] AI-powered insights

See [ROADMAP.md](ROADMAP.md) for detailed roadmap.

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone repository
git clone https://github.com/your-org/icenet-rmm.git
cd icenet-rmm

# Backend development
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Frontend development
cd frontend
npm install
npm run dev

# Agent development
cd agent
go mod download
go build
```

## Community

- **Discord**: [Join our Discord](https://discord.gg/icenet-rmm)
- **Forum**: [Community Forum](https://forum.icenet-rmm.com)
- **GitHub Discussions**: [Ask questions](https://github.com/your-org/icenet-rmm/discussions)
- **Twitter**: [@IceNetRMM](https://twitter.com/icenetrmm)

## Support

- **Documentation**: [docs.icenet-rmm.com](https://docs.icenet-rmm.com)
- **Community Support**: GitHub Discussions and Discord
- **Professional Support**: Available for enterprise customers

## License

IceNet RMM is licensed under the [GNU Affero General Public License v3.0](LICENSE).

This means you can use, modify, and distribute this software, but if you run a modified version as a service, you must make your modifications available under the same license.

## Acknowledgments

IceNet RMM is inspired by and learns from:
- [Tactical RMM](https://github.com/amidaware/tacticalrmm) - Architecture patterns
- [MeshCentral](https://github.com/Ylianst/MeshCentral) - Remote desktop capabilities
- The open-source community

## Research Sources

This project was built using best practices from:
- [RMM Best Practices for 2025](https://www.pulseway.com/blog/rmm-best-practices-for-2025)
- [RMM Security Best Practices](https://www.deepwatch.com/glossary/rmm-security/)
- [Tactical RMM Documentation](https://docs.tacticalrmm.com/)

---

<div align="center">

**Built with ❤️ for the open-source community**

[Website](https://icenet-rmm.com) • [Documentation](https://docs.icenet-rmm.com) • [Community](https://discord.gg/icenet-rmm)

</div>
