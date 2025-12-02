# IceNet RMM Makefile

.PHONY: help dev build test clean docker-up docker-down install-deps

help:
	@echo "IceNet RMM - Development Commands"
	@echo ""
	@echo "  make dev           - Start development environment"
	@echo "  make build         - Build all components"
	@echo "  make test          - Run all tests"
	@echo "  make clean         - Clean build artifacts"
	@echo "  make docker-up     - Start Docker services"
	@echo "  make docker-down   - Stop Docker services"
	@echo "  make install-deps  - Install all dependencies"

dev:
	docker-compose up -d

build:
	@echo "Building backend..."
	cd backend && python -m pip install -r requirements.txt
	@echo "Building frontend..."
	cd frontend && npm install && npm run build
	@echo "Building agent..."
	cd agent && go build -o bin/icenet-agent ./cmd/main.go

test:
	@echo "Running backend tests..."
	cd backend && pytest
	@echo "Running frontend tests..."
	cd frontend && npm test
	@echo "Running agent tests..."
	cd agent && go test ./...

clean:
	@echo "Cleaning build artifacts..."
	rm -rf backend/staticfiles backend/__pycache__
	rm -rf frontend/dist frontend/node_modules
	rm -rf agent/bin

docker-up:
	docker-compose up -d
	@echo "Services starting... Use 'docker-compose logs -f' to view logs"

docker-down:
	docker-compose down

install-deps:
	@echo "Installing Python dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing Node dependencies..."
	cd frontend && npm install
	@echo "Installing Go dependencies..."
	cd agent && go mod download
