# RAG Application Test Suite Documentation

## Overview

This document describes the comprehensive test suite created for the RAG (Retrieval-Augmented Generation) application, including backend unit tests, API integration tests, and Playwright E2E tests.

## Test Structure

```
backend/
  tests/
    test_comprehensive.py       # Core application tests
    test_finetuning_pipeline.py # Fine-tuned embeddings tests
    test_api_integration.py     # HTTP API endpoint tests

frontend/
  e2e/
    embeddings-e2e.spec.js      # Fine-tuning integration E2E
    complete-app.spec.js        # Full application E2E
    chat-page.spec.js           # Chat interface tests
    upload-page.spec.js         # Document upload tests
    new-features.spec.js        # New features tests
    rag-options.spec.js         # RAG configuration tests
```

## Running Tests

### Quick Start - Run All Tests

```bash
# Windows
run-all-tests.bat

# Or manually:
# Backend tests
cd backend
python -m pytest tests/ -v --tb=short

# Frontend E2E tests
cd frontend
npx playwright test
```

### Backend Tests Only

```bash
cd backend

# Run all backend tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_comprehensive.py -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html
```

### Frontend E2E Tests Only

```bash
cd frontend

# Run all E2E tests
npx playwright test

# Run specific test file
npx playwright test embeddings-e2e.spec.js

# Run in headed mode (see browser)
npx playwright test --headed

# Run specific test
npx playwright test -g "should display chat input"

# View test report
npx playwright show-report
```

## Test Categories

### 1. Backend Unit Tests (`test_comprehensive.py`)

Tests core application components:

- **TestEmbeddings**: Embedding generation, dimensions, batch processing
- **TestRAGPipeline**: Retrieval functions, vector store access
- **TestAPIEndpoints**: Schema validation, route registration
- **TestDatabaseModels**: User, Document models
- **TestLLMProviders**: Ollama, OpenAI, Anthropic integration
- **TestDocumentProcessing**: Chunking, text extraction

### 2. Fine-tuning Pipeline Tests (`test_finetuning_pipeline.py`)

Tests for embedding fine-tuning:

- **TestTrainingDataGeneration**: Sample docs, policy synonyms
- **TestFineTunedModel**: Model structure, config validation
- **TestEmbeddingQuality**: Synonym similarity, query-document alignment
- **TestTrainingPipeline**: Loss functions, data loaders
- **TestEvaluationMetrics**: Cosine similarity, MRR, separation metrics

### 3. API Integration Tests (`test_api_integration.py`)

Tests HTTP endpoints directly:

- **TestHealthEndpoints**: `/health`, `/docs`, root endpoint
- **TestDocumentEndpoints**: List, upload, delete documents
- **TestChatEndpoints**: Chat completion, validation
- **TestStreamingEndpoints**: Server-sent events
- **TestRAGOptions**: top_k, use_rag configuration
- **TestCORS**: Cross-origin headers

### 4. E2E Tests (Playwright)

#### `embeddings-e2e.spec.js` (12 tests)

- Document upload flow with embeddings
- Chat with RAG functionality
- RAG options panel
- Mobile responsiveness
- API health checks

#### `complete-app.spec.js` (27 tests)

- Navigation (home, chat, upload)
- Chat interface components
- Provider selection
- Responsive design (6 viewport sizes)
- Error handling (404, empty submit)
- Accessibility (structure, focus, alt text)
- API integration

#### `chat-page.spec.js` (17 tests)

- Chat input field
- Provider selection persistence
- Message display
- RAG context/sources
- Keyboard navigation
- Error handling
- Chat history

#### `upload-page.spec.js` (18 tests)

- Upload interface
- File input validation
- Document list
- Progress indicators
- API integration
- Document preview
- Error handling

## Test Configuration

### Backend (`pytest.ini`)

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = -v --tb=short
```

### Frontend (`playwright.config.js`)

```javascript
{
  testDir: './e2e',
  timeout: 60000,
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: true,
  },
}
```

## Test Results Summary

### Current Status (127 E2E tests total)

| Test File              | Tests | Status             |
| ---------------------- | ----- | ------------------ |
| embeddings-e2e.spec.js | 12    | ✅ 11 pass, 1 skip |
| complete-app.spec.js   | 27    | ✅                 |
| chat-page.spec.js      | 17    | ✅                 |
| upload-page.spec.js    | 18    | ✅                 |
| new-features.spec.js   | 35    | ✅                 |
| rag-options.spec.js    | 12    | ✅                 |
| chat-workflow.spec.js  | 13    | ✅                 |

## Prerequisites

### Backend Tests

- Python 3.10+
- pytest, pytest-asyncio
- httpx (for API tests)
- Application dependencies installed

### Frontend Tests

- Node.js 18+
- Playwright installed (`npx playwright install`)
- Frontend dependencies installed (`npm install`)

## CI/CD Integration

For continuous integration, use:

```yaml
# GitHub Actions example
- name: Run Backend Tests
  run: |
    cd backend
    python -m pytest tests/ -v --junitxml=results.xml

- name: Run E2E Tests
  run: |
    cd frontend
    npx playwright test --reporter=github
```

## Debugging Failed Tests

### Playwright

```bash
# Run with trace
npx playwright test --trace on

# Debug mode
npx playwright test --debug

# View report after failure
npx playwright show-report
```

### Pytest

```bash
# More verbose output
python -m pytest tests/ -vvv

# Stop at first failure
python -m pytest tests/ -x

# Show local variables
python -m pytest tests/ -l
```

## Coverage Goals

- **Unit Tests**: 80%+ code coverage
- **Integration Tests**: All API endpoints
- **E2E Tests**: All user-facing features
- **Accessibility**: WCAG 2.1 AA compliance checks
