# Distributed Event & Notification Engine v1.0

![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg)
![RabbitMQ](https://img.shields.io/badge/RabbitMQ-3.12-ff6600.svg)
![Docker Compose](https://img.shields.io/badge/Docker-Compose-2496ed.svg)

A distributed multi-service architecture featuring a central API Gateway, stateless JWT Authentication Service, RabbitMQ Topic Event Bus, and isolated background notification workers with Dead-Letter Queue (DLQ) failure handling.

---

## Multi-Service Architecture Topology

```
┌────────────────────────────────────────────────────────┐
│                   Public HTTP Request                  │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│               API Gateway (Port 8000)                  │
│   - Receives incoming requests                         │
│   - Proxies token validation to Auth Service           │
└──────────────┬──────────────────────────┬──────────────┘
               │                          │
   (Auth Check)│                          │(Publish Event)
               ▼                          ▼
┌──────────────────────────────┐  ┌──────────────────────┐
│ Central Auth Service (8001)  │  │ RabbitMQ Event Bus   │
│ - JWT Token Verification     │  │ - Topic Exchange     │
│ - Password Hashing           │  │ - Dead-Letter Exchange│
└──────────────────────────────┘  └──────────┬───────────┘
                                             │
                                             ▼
                                  ┌──────────────────────┐
                                  │ Notification Worker  │
                                  │ - Background Consumer│
                                  │ - Multi-Channel Exec │
                                  └──────────────────────┘

```
---

## Service Architecture & Responsibilities

* **API Gateway (services/gateway):** Serves as the single public reverse proxy. Intercepts incoming traffic, enforces centralized auth validation by querying the Auth service, and dispatches events asynchronously to RabbitMQ.

* **Central Auth Service (services/auth):** Handles user registration, bcrypt password hashing, JWT access token issuance, and stateless cryptographic token verification.

* **RabbitMQ Message Broker:** Configured with topic exchanges (events_exchange) for flexible routing (notification.#) and direct dead-letter exchanges (dlx_exchange) for unprocessable messages.

* **Notification Consumer Worker (services/notification):** Asynchronous Python worker utilizing fair prefetch distribution, execution error catching, and dead-letter queue routing upon unrecoverable processing failures.

---

## Key System Design Patterns

* **Distributed Service Decoupling:** Primary HTTP endpoints accept and validate client requests without waiting for downstream email/SMS processing.
* **Stateless Token Verification:** Microservices communicate auth claims securely over internal HTTP loops while preserving single-responsibility identity boundary lines.
* **Fault-Tolerant Message Routing:** RabbitMQ persistent delivery modes combined with worker manual acknowledgements (`basic_ack` / `basic_nack`) ensure zero message loss across broker restarts.
* **Dead-Letter Containment:** Failed background tasks are automatically rerouted to `notification_dlq` to prevent worker thread pool blocking.

---

## Cloud Infrastructure & DevSecOps

* **Kubernetes Orchestration (`k8s/`):** Declarative manifests for API Gateway, Auth Service, Worker, and RabbitMQ with container resource constraints and readiness/liveness probes.
* **Event-Driven Autoscaling (KEDA):** Auto-scales worker replicas from 1 to 10 based on real-time RabbitMQ queue depth thresholds (`k8s/keda-autoscaler.yaml`).
* **DevSecOps & Supply Chain Security:** GitHub Actions pipeline scanning Docker builds with Trivy for OS/package vulnerabilities and deploying tagged container images to GitHub Container Registry (`ghcr.io`).

---

## Quickstart & Deployment
Prerequisites
* Docker & Docker Compose installed

**1. Launch Microservices Mesh**
```
git clone [https://github.com/demmanuel58-spec/event-notification-engine.git]
cd event-notification-engine

# Build and start RabbitMQ, Auth Service, API Gateway, and Workers
docker compose up --build
```

**2. Register a User (Auth Service via Gateway)**
```
curl -X 'POST' \
  'http://localhost:8001/register' \
  -H 'Content-Type: application/json' \
  -d '{
  "username": "dev_user",
  "email": "dev@example.com",
  "password": "SecurePassword123"
}'
```

**3. Obtain JWT Access Token**
```
curl -X 'POST' \
  'http://localhost:8001/token' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=dev_user&password=SecurePassword123'
```

**4. Publish Asynchronous Event via API Gateway**
```
curl -X 'POST' \
  'http://localhost:8000/events/publish' \
  -H 'Authorization: Bearer <YOUR_JWT_ACCESS_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{
  "event_type": "user.registered",
  "email": "dev@example.com",
  "phone": "+1234567890",
  "details": {"campaign": "onboarding_v1"}
}'
```
---

## Author
**David Emmanuel Munyaka**
Backend Software Engineer specializing in distributed systems, REST APIs, and event-driven architecture.

* GitHub: @demmanuel58-spec

* X (Twitter): @David_E_Munyaka

---

## Disclaimer
* **Demonstration & Portfolio Purpose:** This project demonstrates distributed microservices integration, event-driven message queuing with RabbitMQ, and centralized JWT authentication.

* **Production Deployment:** High-availability deployment requires securing inter-service network communication via TLS/mTLS, setting up RabbitMQ cluster mirrors, and externalizing secret management.



































