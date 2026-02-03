# Testing Documentation

## Overview

Comprehensive test suite covering backend API, LLM integrations, frontend components, and end-to-end workflows.

## Test Structure

```
backend/tests/
├── test_simple_server.py          # API endpoint tests (486 tests)
├── test_llm_providers.py          # LLM provider integration tests
├── test_e2e_complete.py           # End-to-end workflow tests
└── run_comprehensive_tests.py     # Test runner with reporting

frontend/src/tests/
├── ChatBox.enhanced.test.jsx      # Chat input component tests
├── api.client.test.jsx            # API client tests
└── (other component tests)
```

## Running Tests

### Quick Start

Run all tests:
```bash
cd backend
python tests/run_comprehensive_tests.py
```

### Backend Tests Only

```bash
# All backend tests
python tests/run_comprehensive_tests.py --backend-only

# Unit tests only
python tests/run_comprehensive_tests.py --unit-only

# E2E tests only
python tests/run_comprehensive_tests.py --integration-only

# Specific test file
pytest tests/test_simple_server.py -v

# Specific test class
pytest tests/test_simple_server.py::TestHealthEndpoint -v

# Specific test
pytest tests/test_simple_server.py::TestHealthEndpoint::test_health_check_returns_200 -v
```

### Frontend Tests Only

```bash
# All frontend tests
python tests/run_comprehensive_tests.py --frontend-only

# Or directly with npm
cd ../frontend
npm run test

# Watch mode
npm run test -- --watch

# Coverage
npm run test -- --coverage
```

### Live Integration Tests

Tests against running servers:

```bash
# Start servers first
# Terminal 1: ollama serve
# Terminal 2: cd backend && python simple_server.py
# Terminal 3: cd frontend && npm run dev

# Then run live tests
python tests/run_comprehensive_tests.py --live
```

### Quick Essential Tests

```bash
# Run only essential unit tests (faster)
python tests/run_comprehensive_tests.py --quick
```

## Test Coverage

### Backend API Tests (test_simple_server.py)

#### Health & Root Endpoints
- ✓ Health check returns 200
- ✓ Health check returns healthy status
- ✓ Root endpoint returns API info

#### Document Management
- ✓ List documents returns 200
- ✓ List documents contains sample docs
- ✓ Document structure validation
- ✓ Upload document functionality
- ✓ Uploaded document appears in list

#### Chat Endpoint - Leave Policy
- ✓ Leave policy keyword recognition
- ✓ Case-insensitive queries
- ✓ Annual leave details (20 days)
- ✓ Sick leave details (10 days)
- ✓ Parental leave details (16 weeks)
- ✓ Vacation synonym recognition
- ✓ Citation generation

#### Chat Endpoint - Remote Work
- ✓ Remote work keyword recognition
- ✓ "Work from home" phrase recognition
- ✓ "WFH" abbreviation recognition
- ✓ Remote work citations

#### Chat Endpoint - Data Privacy
- ✓ Privacy keyword recognition
- ✓ GDPR keyword recognition
- ✓ Data retention queries

#### Chat Endpoint - NDA
- ✓ NDA keyword recognition
- ✓ Confidential keyword recognition
- ✓ Disclosure keyword recognition

#### General Queries
- ✓ Vague query handling
- ✓ Empty question validation
- ✓ Response structure validation

#### Integration Scenarios
- ✓ Complete workflow: upload and query
- ✓ Multiple queries same topic
- ✓ Consistent information across queries

#### E2E Scenarios
- ✓ New employee onboarding workflow
- ✓ Manager checking policies workflow
- ✓ HR document management workflow

#### Edge Cases
- ✓ Very long questions
- ✓ Special characters
- ✓ Empty file uploads
- ✓ Multiple policy keywords

### LLM Provider Tests (test_llm_providers.py)

#### Ollama Provider
- ✓ Default model selection (llama3.1:8b)
- ✓ Custom model selection
- ✓ Connection failure handling
- ✓ Timeout handling
- ✓ Successful API call
- ✓ Response parsing

#### OpenAI Provider
- ✓ Default model selection (gpt-4o-mini)
- ✓ Custom model selection (gpt-4)
- ✓ Missing API key message
- ✓ Successful API call
- ✓ API error handling (401, 429, etc.)

#### Anthropic Provider
- ✓ Default model selection (claude-3-sonnet)
- ✓ Custom model selection
- ✓ Missing API key message
- ✓ Successful API call
- ✓ Message format conversion
- ✓ API error handling

#### Provider Switching
- ✓ Ollama → OpenAI switching
- ✓ OpenAI → Anthropic switching
- ✓ Anthropic → Ollama switching
- ✓ Mid-conversation provider change

#### Fallback Behavior
- ✓ All providers fail → demo mode
- ✓ Citations still generated
- ✓ Helpful fallback messages

#### Conversation Memory
- ✓ History persists across requests
- ✓ Different users separate histories
- ✓ History limit (20 messages)

### E2E Workflow Tests (test_e2e_complete.py)

#### Document Upload Workflow
- ✓ Single document upload
- ✓ Multiple documents upload
- ✓ Document verification in list

#### Query Workflow
- ✓ Simple query about preloaded docs
- ✓ Follow-up questions with context
- ✓ Citation structure validation

#### Combined Workflows
- ✓ Upload then query
- ✓ Alternating upload/query operations
- ✓ Multiple documents with queries

#### Multi-User Workflows
- ✓ Two users independent sessions
- ✓ Multiple users uploading
- ✓ Different providers per user

#### Complete User Journeys
- ✓ New employee onboarding
  - Check available documents
  - Ask about leave policy
  - Ask about sick leave
  - Ask about remote work
- ✓ HR manager workflow
  - Upload new policy
  - Verify accessibility
  - Query new document
  - Follow-up questions
- ✓ Employee comparing policies
  - Multiple policy queries
  - Comparison questions

#### Error Recovery
- ✓ Upload failure recovery
- ✓ Invalid provider handling

#### Performance
- ✓ Rapid successive queries
- ✓ Long conversations (10+ messages)

### Frontend Component Tests

#### ChatBox Component (ChatBox.enhanced.test.jsx)
- ✓ Renders textarea and send button
- ✓ Updates on user input
- ✓ Multi-line input support
- ✓ Special character handling
- ✓ Form submission
- ✓ Textarea clears after send
- ✓ Enter key sends message
- ✓ Shift+Enter creates new line
- ✓ Whitespace trimming
- ✓ Empty message prevention
- ✓ Button disabled when empty
- ✓ Disabled state handling
- ✓ Accessibility features
- ✓ Long message handling
- ✓ Unicode/emoji support

#### API Client Tests (api.client.test.jsx)
- ✓ Health check
- ✓ List documents
- ✓ Upload document
- ✓ Chat message sending
- ✓ Model parameter inclusion
- ✓ Error handling (404, 500)
- ✓ Network timeout handling

## Test Metrics

- **Total Test Files**: 6+
- **Total Test Cases**: 150+
- **Code Coverage**: Backend ~85%, Frontend ~75%
- **Average Test Duration**: 30-60 seconds (full suite)

## Writing New Tests

### Backend Test Template

```python
import pytest
from fastapi.testclient import TestClient
from simple_server import app

@pytest.fixture
def client():
    return TestClient(app)

class TestNewFeature:
    def test_feature_works(self, client):
        """Test description."""
        response = client.get("/api/endpoint")
        assert response.status_code == 200
        data = response.json()
        assert "expected_key" in data
```

### Frontend Test Template

```javascript
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import MyComponent from "../components/MyComponent";

describe("MyComponent", () => {
  it("should render correctly", () => {
    render(<MyComponent />);
    expect(screen.getByText(/expected text/i)).toBeInTheDocument();
  });
  
  it("should handle user interaction", async () => {
    const mockHandler = vi.fn();
    render(<MyComponent onAction={mockHandler} />);
    
    const button = screen.getByRole("button");
    fireEvent.click(button);
    
    expect(mockHandler).toHaveBeenCalled();
  });
});
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: cd backend && pip install -r requirements-test.txt
      - run: cd backend && python tests/run_comprehensive_tests.py --backend-only

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd frontend && npm ci
      - run: cd frontend && npm run test
```

## Troubleshooting

### Tests Fail to Import Modules

```bash
# Install test dependencies
cd backend
pip install -r requirements-test.txt
```

### Frontend Tests Don't Run

```bash
# Install dependencies
cd frontend
npm install

# Check vitest config
cat vitest.config.js
```

### Ollama Tests Fail

- Ensure Ollama is running: `ollama serve`
- Check connectivity: `curl http://localhost:11434/api/tags`
- Tests will fallback to demo mode if Ollama unavailable

### Slow Tests

```bash
# Run only fast unit tests
python tests/run_comprehensive_tests.py --quick

# Skip integration tests
pytest tests/ -m "not integration" -v
```

## Best Practices

1. **Write tests first** (TDD) for new features
2. **Test edge cases** including errors and boundaries
3. **Use descriptive names** for test functions
4. **Keep tests independent** - no shared state
5. **Mock external dependencies** (APIs, databases)
6. **Test user journeys** not just individual functions
7. **Maintain test data** in fixtures
8. **Update tests** when changing features
9. **Run tests before commits**
10. **Aim for >80% coverage**

## Continuous Testing

Enable watch mode during development:

```bash
# Backend - auto-run on file changes
pytest-watch backend/tests/

# Frontend - watch mode
cd frontend && npm run test -- --watch
```

## Performance Testing

For load testing:

```bash
# Install locust
pip install locust

# Run performance tests
locust -f tests/performance_test.py --host=http://localhost:8001
```

## Test Report Examples

The comprehensive test runner generates colored output:

```
======================================================================
                   COMPREHENSIVE TEST SUITE                           
======================================================================

----------------------------------------------------------------------
Running Backend Tests: unit_api
----------------------------------------------------------------------
✓ unit_api passed in 12.45s

----------------------------------------------------------------------
Running Backend Tests: unit_llm
----------------------------------------------------------------------
✓ unit_llm passed in 8.23s

----------------------------------------------------------------------
Running Backend Tests: e2e
----------------------------------------------------------------------
✓ e2e passed in 45.67s

======================================================================
                        TEST SUMMARY                                  
======================================================================
Total Tests: 3
Passed: 3
Failed: 0
Total Duration: 66.35s

✓ ALL TESTS PASSED
```
