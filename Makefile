# SimpleCrawler Makefile - Microservices Edition

# Docker and Compose
COMPOSE = docker-compose
COMPOSE_FILE = docker-compose.yml

# Services
API_SERVICE = api
WORKER_SERVICE = worker
DB_SERVICE = postgres
REDIS_SERVICE = redis

.PHONY: help build up down logs test clean restart status api-logs worker-logs db-logs

help: ## Show this help message
	@echo "SimpleCrawler MK4 - Microservices Commands:"
	@echo
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

# Core Docker Compose commands
build: ## Build all services
	$(COMPOSE) build

up: ## Start all services
	$(COMPOSE) up -d

down: ## Stop and remove all services
	$(COMPOSE) down

restart: ## Restart all services
	$(COMPOSE) restart

stop: ## Stop all services
	$(COMPOSE) stop

# Development commands
dev: ## Start services in development mode (with logs)
	$(COMPOSE) up --build

dev-api: ## Start only API and dependencies for development
	$(COMPOSE) up --build postgres redis api

dev-worker: ## Start worker and dependencies for development
	$(COMPOSE) up --build postgres redis worker

# Logging and monitoring
logs: ## Show logs for all services
	$(COMPOSE) logs -f

api-logs: ## Show API service logs
	$(COMPOSE) logs -f $(API_SERVICE)

worker-logs: ## Show worker service logs
	$(COMPOSE) logs -f $(WORKER_SERVICE)

db-logs: ## Show database logs
	$(COMPOSE) logs -f $(DB_SERVICE)

redis-logs: ## Show Redis logs
	$(COMPOSE) logs -f $(REDIS_SERVICE)

# Status and health
status: ## Show service status
	$(COMPOSE) ps

health: ## Check service health
	@echo "🔍 Service Health Check:"
	@echo "========================"
	@curl -s http://localhost:8000/health | python -m json.tool 2>/dev/null || echo "❌ API not responding"

stats: ## Show API statistics
	@echo "📊 API Statistics:"
	@echo "=================="
	@curl -s http://localhost:8000/stats | python -m json.tool 2>/dev/null || echo "❌ API not responding"

# Database operations
db-shell: ## Connect to database shell
	$(COMPOSE) exec $(DB_SERVICE) psql -U crawler -d crawler_db

db-reset: ## Reset database (WARNING: destroys all data)
	$(COMPOSE) down -v
	$(COMPOSE) up -d postgres
	@echo "⚠️  Database reset complete"

# Redis operations
redis-shell: ## Connect to Redis CLI
	$(COMPOSE) exec $(REDIS_SERVICE) redis-cli

redis-monitor: ## Monitor Redis activity
	$(COMPOSE) exec $(REDIS_SERVICE) redis-cli monitor

queue-stats: ## Show queue statistics
	@echo "📊 Queue Status:"
	@echo "================"
	@$(COMPOSE) exec $(REDIS_SERVICE) redis-cli llen crawl_queue || echo "❌ Redis not responding"

# Testing and API interaction
test-quick: ## Test quick crawl endpoint
	curl -X POST "http://localhost:8000/crawl/quick?url=https://example.com&pages=2&format=json" | python -m json.tool

test-crawl: ## Test full crawl endpoint
	curl -X POST "http://localhost:8000/crawl" \
		-H "Content-Type: application/json" \
		-d '{"start_url": "https://example.com", "max_pages": 5, "export_format": "json"}' | python -m json.tool

list-jobs: ## List all crawl jobs
	curl -s "http://localhost:8000/jobs" | python -m json.tool

# Scaling
scale-workers: ## Scale worker instances (usage: make scale-workers WORKERS=3)
	$(COMPOSE) up -d --scale $(WORKER_SERVICE)=$(or $(WORKERS),2)

# Maintenance
clean: ## Clean up containers, networks, and volumes
	$(COMPOSE) down -v --remove-orphans
	docker system prune -f

clean-all: ## Clean everything including images
	$(COMPOSE) down -v --remove-orphans --rmi all
	docker system prune -af

backup: ## Backup database and Redis data
	@echo "💾 Creating backup..."
	mkdir -p backups
	$(COMPOSE) exec -T $(DB_SERVICE) pg_dump -U crawler crawler_db > backups/db_backup_$(shell date +%Y%m%d_%H%M%S).sql
	$(COMPOSE) exec -T $(REDIS_SERVICE) redis-cli bgsave
	@echo "✅ Backup created in backups/"

# Production deployment
deploy: ## Deploy to production (build and start)
	$(COMPOSE) -f docker-compose.yml build
	$(COMPOSE) -f docker-compose.yml up -d

# API documentation
docs: ## Open API documentation
	@echo "📚 Opening API docs at http://localhost:8000/docs"
	@which xdg-open >/dev/null && xdg-open http://localhost:8000/docs || echo "Open http://localhost:8000/docs in your browser"

# Service-specific operations
api-restart: ## Restart API service only
	$(COMPOSE) restart $(API_SERVICE)

worker-restart: ## Restart worker services only
	$(COMPOSE) restart $(WORKER_SERVICE)

api-rebuild: ## Rebuild and restart API service
	$(COMPOSE) build $(API_SERVICE)
	$(COMPOSE) up -d $(API_SERVICE)

worker-rebuild: ## Rebuild and restart worker services
	$(COMPOSE) build $(WORKER_SERVICE)
	$(COMPOSE) up -d $(WORKER_SERVICE)

# Legacy single-process commands (still available)
setup: ## Setup development environment (legacy)
	@echo "⚠️  Legacy command. Use 'make build && make up' for microservices"

test-real-sites: ## Test with real sites (legacy)
	@echo "⚠️  Use API endpoints instead: make test-crawl"

# Quick start
quick-start: build up health ## Quick start: build, start, and health check
	@echo "🚀 SimpleCrawler MK4 is ready!"
	@echo "📚 API docs: http://localhost:8000/docs"
	@echo "📊 Health: http://localhost:8000/health"