# Contributing to SimpleCrawler MK4

We welcome contributions! This guide will help you get started.

## 🏗️ Architecture Overview

SimpleCrawler MK4 is a microservices platform with:

- **API Service**: FastAPI + Pydantic (REST API)
- **Worker Service**: Background job processing
- **PostgreSQL**: Job persistence and state management
- **Redis**: Job queue and caching
- **Nginx**: Reverse proxy and load balancing

## 🛠️ Development Setup

### Prerequisites
- Docker and Docker Compose
- Make (for build automation)
- Git

### Getting Started

```bash
# Clone the repository
git clone https://github.com/yourusername/SimpleCrawler-MK4.git
cd SimpleCrawler-MK4

# Start development environment
make dev

# Run tests
make test

# Check service health
make health
```

## 📝 Making Changes

### Code Structure

- **`services/api/`**: FastAPI REST API service
- **`services/worker/`**: Background job processors
- **`app/`**: Core crawler engine (shared between API and workers)
- **`docs/`**: Documentation
- **`examples/`**: Usage examples and demos

### Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow existing code patterns
   - Add tests for new functionality
   - Update documentation if needed

3. **Test your changes**
   ```bash
   # Run unit tests
   make test
   
   # Test specific services
   make api-logs
   make worker-logs
   
   # Test with real sites
   make test-real-sites
   ```

4. **Check code quality**
   ```bash
   # Format code
   make format
   
   # Check linting
   make lint
   ```

5. **Test the full stack**
   ```bash
   # Rebuild affected services
   make api-rebuild
   make worker-rebuild
   
   # Verify health
   make health
   ```

## 🧪 Testing Guidelines

### Unit Tests
- Add tests in `app/tests/`
- Use pytest with async support
- Mock external dependencies

### Integration Tests
- Test API endpoints with real HTTP calls
- Test worker job processing
- Test database interactions

### Real-World Testing
```bash
# Test against real documentation sites
make test-real-sites

# Test code extraction
python test_code_extraction.py

# Test readable formats
make test-readable-formats
```

## 🐳 Docker Development

### Building Services
```bash
# Build all services
make build

# Build specific service
make api-rebuild
make worker-rebuild
```

### Service Logs
```bash
# All services
make logs

# Specific service
make api-logs
make worker-logs
make db-logs
```

## 📊 API Development

### Adding New Endpoints

1. **Add Pydantic models** in `services/api/main.py`
2. **Implement endpoint logic**
3. **Add proper error handling**
4. **Update API documentation**
5. **Add tests**

### Example:
```python
class NewFeatureRequest(BaseModel):
    param1: str = Field(..., description="Required parameter")
    param2: int = Field(default=10, ge=1, le=100)

@app.post("/new-feature", response_model=NewFeatureResponse)
async def new_feature(request: NewFeatureRequest):
    # Implementation
    return NewFeatureResponse(...)
```

## 🔄 Worker Development

### Adding New Job Types

1. **Update worker logic** in `services/worker/worker.py`
2. **Add job type handling**
3. **Update database schema if needed**
4. **Add proper error handling**
5. **Test job processing**

## 📚 Documentation

### Adding Documentation
- Update `README.md` for user-facing changes
- Add technical docs in `docs/`
- Update API documentation
- Add examples for new features

### Documentation Standards
- Use clear, concise language
- Include code examples
- Add screenshots for UI changes
- Update changelog

## 🚀 Deployment

### Testing Deployment
```bash
# Production-like build
make deploy

# Check all services
make status
make health
```

### Environment Variables
- Document new environment variables
- Provide sensible defaults
- Update docker-compose.yml

## 📋 Pull Request Guidelines

### Before Submitting
- [ ] Code follows existing patterns
- [ ] Tests pass (`make test`)
- [ ] Documentation updated
- [ ] Services build successfully (`make build`)
- [ ] Health checks pass (`make health`)
- [ ] No lint errors (`make lint`)

### PR Description
Include:
- **What**: Brief description of changes
- **Why**: Motivation for the change
- **How**: Technical implementation details
- **Testing**: How you tested the changes

### Example PR Template
```markdown
## What
Added support for XML export format

## Why
Users requested XML output for integration with legacy systems

## How
- Added XMLExporter class in app/exporters.py
- Updated API to accept 'xml' format parameter
- Added XML validation and tests

## Testing
- Unit tests for XML exporter
- Integration test with sample crawl
- Validated XML output with xmllint
```

## 🐛 Bug Reports

### Creating Issues
Use the issue template and include:
- **Environment**: OS, Docker version, etc.
- **Steps to reproduce**
- **Expected behavior**
- **Actual behavior**
- **Logs**: Relevant service logs
- **Screenshots**: If applicable

### Debugging
```bash
# Get service logs
make logs

# Check service status
make status

# Database inspection
make db-shell

# Redis inspection
make redis-shell
```

## 🏆 Code Quality

### Standards
- **Type hints**: Use type annotations
- **Docstrings**: Document functions and classes
- **Error handling**: Graceful error recovery
- **Logging**: Appropriate log levels
- **Performance**: Consider async/await patterns

### Tools
- **Black**: Code formatting
- **Flake8**: Linting
- **Pytest**: Testing
- **MyPy**: Type checking (optional)

## 🎯 Release Process

### Versioning
We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking API changes
- **MINOR**: New features, backwards compatible
- **PATCH**: Bug fixes

### Release Checklist
- [ ] Update version numbers
- [ ] Update CHANGELOG.md
- [ ] Test full deployment
- [ ] Tag release
- [ ] Update documentation

## 💬 Getting Help

- **Issues**: GitHub Issues for bugs and feature requests
- **Discussions**: GitHub Discussions for questions
- **Documentation**: Check `docs/` directory
- **Examples**: Look at `examples/` directory

## 📜 Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Follow the golden rule

Thank you for contributing to SimpleCrawler MK4! 🚀