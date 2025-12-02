# IceNet RMM - Architecture Documentation

## Overview

IceNet RMM is a secure, open-source Remote Monitoring and Management solution designed for cross-platform endpoint management with enterprise-grade security.

## Design Principles

1. **Security First**: Zero-trust architecture with defense in depth
2. **Cross-Platform**: Native support for Windows and Linux systems
3. **Scalability**: Designed to manage from 10 to 10,000+ endpoints
4. **Real-Time**: Instant communication and updates via messaging layer
5. **Modular**: Loosely coupled components for maintainability

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Web Browser (Client)                    │
│                    Vue.js 3 + TypeScript                     │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS/WSS
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                     Nginx (Reverse Proxy)                    │
│              TLS Termination, Load Balancing                 │
└──────┬────────────────────────────────────────────┬─────────┘
       │                                             │
       ▼                                             ▼
┌──────────────────┐                    ┌──────────────────────┐
│  Django Backend  │◄───────────────────┤   NATS Message Bus   │
│  REST API + WS   │                    │   (Real-time Comms)  │
└────┬─────────────┘                    └──────────┬───────────┘
     │                                             │
     │  ┌──────────────────────────────────────────┘
     │  │
     ▼  ▼
┌─────────────────────────────────────────────────────────────┐
│                      PostgreSQL Database                     │
│           (Agents, Users, Policies, Audit Logs)             │
└─────────────────────────────────────────────────────────────┘
     │
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Redis (Cache + Queue)                     │
│                Celery Task Queue for Jobs                    │
└─────────────────────────────────────────────────────────────┘

     ▲                                             ▲
     │ HTTPS + NATS                                │
     │                                             │
┌────┴─────────────────┐              ┌───────────┴──────────┐
│  Windows Agent (Go)  │              │  Linux Agent (Go)    │
│  - System Monitor    │              │  - System Monitor    │
│  - Update Manager    │              │  - Update Manager    │
│  - Command Executor  │              │  - Command Executor  │
│  - RDP Service       │              │  - VNC/SSH Service   │
└──────────────────────┘              └──────────────────────┘
```

## Core Components

### 1. Backend Server (Django + Python)

**Responsibilities:**
- REST API for all operations (CRUD for agents, users, policies)
- WebSocket server for real-time updates to frontend
- Authentication and authorization (JWT + MFA)
- Agent registration and management
- Task scheduling and orchestration
- Audit logging and compliance
- Integration with NATS for agent communication

**Technology Stack:**
- Django 5.x with Django REST Framework
- Django Channels for WebSocket support
- PostgreSQL for relational data
- Redis for caching and Celery broker
- Celery for background task processing

**Key Features:**
- Role-Based Access Control (RBAC)
- Multi-tenancy support (organizations/clients)
- API rate limiting and throttling
- Comprehensive audit logging
- TOTP/FIDO2 MFA support

### 2. Frontend Web Control Panel (Vue.js)

**Responsibilities:**
- Modern, responsive dashboard
- Real-time agent status monitoring
- Remote desktop interface
- Software update management
- Alert and notification center
- Reporting and analytics
- User and policy management

**Technology Stack:**
- Vue 3 with Composition API
- TypeScript for type safety
- Pinia for state management
- Vue Router for navigation
- Vite for fast builds
- Tailwind CSS for styling
- Chart.js for visualizations

**Key Features:**
- Real-time dashboard with WebSocket updates
- Multi-tabbed remote desktop sessions
- Drag-and-drop file upload/download
- Advanced filtering and search
- Dark mode support
- Mobile-responsive design

### 3. Cross-Platform Agent (Go)

**Responsibilities:**
- System monitoring (CPU, RAM, disk, network)
- Installed software inventory
- OS and software updates
- Remote command execution
- File operations
- Remote desktop service
- Secure communication with server
- Auto-update capability

**Technology Stack:**
- Go 1.21+ for performance and cross-compilation
- NATS client for messaging
- Cryptographic libraries for secure communication
- Platform-specific APIs (Win32 API, Linux syscalls)

**Agent Features:**

*Windows Agent:*
- Windows Update integration
- Chocolatey/Winget for app updates
- RDP service with authentication
- Event Log monitoring
- Registry monitoring
- Service management

*Linux Agent:*
- APT/YUM/DNF package management
- Systemd service management
- VNC/X11 remote desktop
- Log file monitoring
- Cron job management

**Security Features:**
- Certificate-based authentication
- Encrypted communication (TLS 1.3)
- Code signing for updates
- Sandboxed command execution
- Privilege escalation controls

### 4. NATS Message Bus

**Responsibilities:**
- Real-time bidirectional communication
- Pub/sub messaging patterns
- Request/reply patterns
- Load balancing across agents

**Why NATS:**
- High performance (millions of msgs/sec)
- Lightweight and simple
- Built-in security (TLS, authentication)
- Clustering and high availability
- Small footprint

### 5. Remote Desktop Service

**Implementation Options:**

**Option A: MeshCentral Integration**
- Proven, mature solution
- Built-in Intel AMT support
- WebRTC-based
- Easy integration

**Option B: Custom WebRTC Solution**
- Full control over features
- Lighter weight
- Direct integration with our auth system

**Recommended: Start with MeshCentral integration, build custom later if needed**

### 6. Update Management Service

**OS Updates:**

*Windows:*
- Windows Update API integration
- WSUS support for enterprise
- Update approval workflows
- Rollback capability

*Linux:*
- APT (Debian/Ubuntu)
- YUM/DNF (RedHat/CentOS/Fedora)
- Pacman (Arch)
- Zypper (SUSE)

**Application Updates:**

*Windows:*
- Chocolatey integration
- Winget support
- Custom MSI/EXE installers

*Linux:*
- Package manager integration
- Flatpak/Snap support
- Custom scripts

**Update Policy Engine:**
- Maintenance windows
- Staged rollouts
- Automatic/manual approval
- Dependency resolution
- Reboot scheduling

## Security Architecture

### Authentication & Authorization

1. **User Authentication:**
   - Username/password with argon2 hashing
   - Mandatory MFA (TOTP or FIDO2)
   - Session management with JWT
   - OAuth2/OIDC integration for SSO
   - Rate limiting on auth endpoints

2. **Agent Authentication:**
   - Mutual TLS (mTLS) with client certificates
   - Agent registration tokens (one-time use)
   - Certificate rotation every 90 days
   - Hardware-based identity where available

3. **Authorization:**
   - Role-Based Access Control (RBAC)
   - Granular permissions (read, write, execute, delete)
   - Multi-tenancy with data isolation
   - Audit logging of all actions

### Network Security

1. **Encryption:**
   - TLS 1.3 for all communications
   - End-to-end encryption for sensitive data
   - Encrypted database fields (PII, credentials)
   - Secure key storage (HashiCorp Vault integration)

2. **Network Segmentation:**
   - Separate networks for management and agents
   - Firewall rules with least privilege
   - VPN/zero-trust network access
   - Optional agent-to-agent isolation

3. **DDoS Protection:**
   - Rate limiting at nginx level
   - Connection throttling
   - IP whitelisting/blacklisting
   - Cloudflare/WAF integration

### Application Security

1. **Input Validation:**
   - Strict input sanitization
   - Parameterized queries (SQL injection prevention)
   - XSS protection headers
   - CSRF tokens

2. **Dependency Management:**
   - Regular dependency updates
   - Vulnerability scanning (Dependabot, Snyk)
   - Supply chain verification
   - SBOM (Software Bill of Materials)

3. **Code Security:**
   - Code signing for all releases
   - Secure development lifecycle
   - Regular security audits
   - Penetration testing

### Audit & Compliance

1. **Comprehensive Logging:**
   - All user actions logged
   - All agent commands logged
   - Authentication attempts
   - Configuration changes
   - System events

2. **Log Management:**
   - Centralized logging (ELK/Loki)
   - Log retention policies
   - Tamper-proof logging
   - Real-time alerting

3. **Compliance:**
   - SOC 2 Type II compatible
   - GDPR compliance
   - HIPAA considerations
   - ISO 27001 alignment

## Database Schema (High-Level)

### Core Tables:

**organizations**
- Multi-tenancy support
- Billing information
- Settings and preferences

**users**
- Authentication credentials
- MFA settings
- Roles and permissions
- Audit trail

**agents**
- Agent identity and registration
- System information
- Last seen timestamp
- Status and health metrics
- Associated organization

**agent_data**
- Time-series metrics (CPU, RAM, disk)
- Installed software inventory
- System configuration
- Network interfaces

**policies**
- Update policies
- Security policies
- Monitoring policies
- Scheduled tasks

**tasks**
- Pending commands/jobs
- Task status and results
- Scheduled tasks
- Task history

**audit_logs**
- User actions
- Agent actions
- System events
- Security events

**updates**
- Available updates
- Update history
- Approval status
- Rollback information

## Deployment Architecture

### Production Deployment

**Recommended Setup:**

```
┌────────────────────────────────────────────────────┐
│              Load Balancer (HA Proxy)              │
└────────────────┬───────────────────────────────────┘
                 │
         ┌───────┴────────┐
         ▼                ▼
┌─────────────────┐  ┌─────────────────┐
│  Nginx Server 1 │  │  Nginx Server 2 │
└────────┬────────┘  └────────┬────────┘
         │                    │
         └────────┬───────────┘
                  ▼
         ┌─────────────────┐
         │ Django Cluster  │
         │  (3+ workers)   │
         └────────┬────────┘
                  │
         ┌────────┴────────────────────┐
         ▼                             ▼
┌─────────────────┐         ┌─────────────────────┐
│  PostgreSQL HA  │         │   NATS Cluster      │
│  (Primary/Rep)  │         │   (3 nodes)         │
└─────────────────┘         └─────────────────────┘
         ▼
┌─────────────────┐
│  Redis Cluster  │
│  (Sentinel)     │
└─────────────────┘
```

**Docker Compose for Development:**
- All services containerized
- Easy local development
- Consistent environments

**Kubernetes for Enterprise:**
- Auto-scaling
- Self-healing
- Rolling updates
- Service mesh (Istio)

## Performance & Scalability

### Design for Scale:

1. **Horizontal Scaling:**
   - Stateless application servers
   - Database read replicas
   - NATS clustering
   - Redis clustering

2. **Caching Strategy:**
   - Redis for session data
   - Query result caching
   - CDN for static assets
   - Agent data aggregation

3. **Database Optimization:**
   - Proper indexing
   - Query optimization
   - Connection pooling
   - Partitioning for time-series data

4. **Performance Targets:**
   - API response time: < 100ms (p95)
   - Agent check-in: < 30 seconds
   - Real-time updates: < 1 second latency
   - Support 10,000+ concurrent agents

## Monitoring & Observability

1. **Metrics:**
   - Prometheus for metrics collection
   - Grafana for visualization
   - Custom dashboards

2. **Logging:**
   - Structured logging (JSON)
   - ELK stack or Loki
   - Log aggregation and search

3. **Tracing:**
   - Distributed tracing (Jaeger/Zipkin)
   - Request flow visualization
   - Performance bottleneck identification

4. **Alerting:**
   - PagerDuty/Opsgenie integration
   - Alert rules for critical events
   - Escalation policies

## Development Workflow

1. **Version Control:**
   - Git with feature branch workflow
   - Protected main branch
   - Required code reviews
   - Automated testing in CI

2. **CI/CD Pipeline:**
   - GitHub Actions / GitLab CI
   - Automated testing (unit, integration, e2e)
   - Security scanning
   - Automated deployments

3. **Testing Strategy:**
   - Unit tests (>80% coverage)
   - Integration tests
   - E2E tests with Playwright
   - Load testing with k6

4. **Documentation:**
   - API documentation (OpenAPI/Swagger)
   - User documentation
   - Admin documentation
   - Developer documentation

## Roadmap

**Phase 1: Foundation (Months 1-2)**
- Core backend API
- Agent development (basic monitoring)
- Basic web dashboard
- Agent-server communication

**Phase 2: Core Features (Months 3-4)**
- Update management
- Remote command execution
- User management and RBAC
- Audit logging

**Phase 3: Advanced Features (Months 5-6)**
- Remote desktop integration
- Advanced monitoring and alerting
- Automated remediation
- Reporting and analytics

**Phase 4: Enterprise Features (Months 7-8)**
- Multi-tenancy
- SSO integration
- Advanced security features
- API webhooks and integrations

**Phase 5: Scale & Polish (Months 9-10)**
- Performance optimization
- HA and clustering
- Mobile app
- Marketplace/plugin system

## Technology Decisions - Rationale

### Why Django?
- Mature, battle-tested framework
- Excellent ORM
- Built-in admin interface
- Large ecosystem
- Security features out-of-the-box

### Why Vue.js?
- Progressive framework
- Excellent documentation
- Great performance
- Easy to learn
- TypeScript support

### Why Go for Agent?
- Cross-compilation for multiple platforms
- Small binary size
- Fast execution
- Low resource usage
- Great standard library

### Why NATS?
- Lightweight and fast
- Easy to deploy
- Built-in security
- Excellent Go client
- Proven at scale

### Why PostgreSQL?
- ACID compliance
- JSON support
- Full-text search
- Excellent performance
- Rich ecosystem

## Security Lessons from Existing RMM Solutions

**Kaseya VSA Attack (2021):**
- Lesson: Supply chain security is critical
- Solution: Code signing, secure update mechanism

**ConnectWise Vulnerabilities:**
- Lesson: Authentication bypasses are common
- Solution: Security-first development, regular audits

**Common Issues:**
- Weak default credentials
- Insufficient access controls
- Lack of audit logging
- Insecure update mechanisms

**Our Approach:**
- No default credentials
- Mandatory MFA
- Comprehensive audit logging
- Signed, verified updates
- Zero-trust architecture

## References

This architecture draws inspiration from:
- Tactical RMM (open-source RMM)
- MeshCentral (remote desktop)
- Prometheus (monitoring)
- Kubernetes (orchestration patterns)
- NIST Cybersecurity Framework
- OWASP Top 10

## Contributing

See CONTRIBUTING.md for development guidelines.

## License

IceNet RMM is licensed under a Dual License model:
- **Non-Commercial License**: Free for personal, educational, research, and non-profit use
- **Commercial License**: Required for commercial use (contact for licensing)

Copyright (c) 2025 Northern Plains IT, LLC and OnyxVZ, LLC. All Rights Reserved.

See LICENSE file for complete terms.
