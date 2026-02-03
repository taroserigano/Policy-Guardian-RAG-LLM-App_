# Testing Guide - Policy RAG Application

## Overview

This document describes the testing strategy, test suites, and how to run tests for the Policy RAG application.

## Test Structure

### Backend Tests

#### 1. Unit Tests (`backend/tests/run_tests.py`)

Simplified test suite that validates core components without external dependencies.

**Test Coverage:**

- ✅ Configuration loading (Pydantic settings)
- ✅ Pydantic schema validation
- ✅ Database models (SQLAlchemy ORM)
- ✅ Utility functions (filename sanitization)
- ✅ Text chunking (RecursiveCharacterTextSplitter)
- ✅ Schema validation (error handling)

**Running Unit Tests:**

```bash
cd backend
python tests/run_tests.py
```

**Expected Output:**

```
=====================================================================
POLICY RAG APPLICATION - TEST SUITE
=====================================================================

[TEST 1] Testing Configuration...
✅ Configuration: PASSED

[TEST 2] Testing Pydantic Schemas...
✅ Schemas: PASSED

[TEST 3] Testing Database Models...
✅ Database Models: PASSED

[TEST 4] Testing Utility Functions...
✅ Utility Functions: PASSED

[TEST 5] Testing Text Chunking...
✅ Text Chunking: PASSED (created 6 chunks)

[TEST 6] Testing Schema Validation...
✅ Schema Validation: PASSED (caught empty question)
✅ Schema Validation: PASSED (caught missing fields)

=====================================================================
TEST SUITE COMPLETED
=====================================================================

✅ All core components tested successfully!
```

#### 2. Integration Tests (`backend/tests/integration_test.py`)

Full API tests that require PostgreSQL, Pinecone, and Ollama to be running.

**Test Coverage:**

- ✅ Health check endpoint
- ✅ Document upload with file handling
- ✅ Document listing
- ✅ Chat query with RAG pipeline
- ✅ Chat with document filtering
- ✅ Error handling and validation

**Prerequisites:**

1. PostgreSQL running on port 5432
2. Ollama running locally with llama3.1 model
3. Pinecone API key configured in `.env`
4. Backend dependencies installed

**Running Integration Tests:**

```bash
# Start required services first
docker-compose up -d postgres

# Install Ollama and pull model
ollama pull llama3.1

# Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env and add your PINECONE_API_KEY

# Run integration tests
cd backend
python tests/integration_test.py
```

**Expected Output:**

```
======================================================================
  POLICY RAG APPLICATION - INTEGRATION TEST SUITE
======================================================================

Setting up database...
✅ Database initialized

======================================================================
  TEST 1: Health Check
======================================================================

Status Code: 200
Response: {'status': 'healthy', 'version': '1.0.0'}
✅ Health check passed

======================================================================
  TEST 2: Document Upload
======================================================================

Status Code: 200
Response: {'success': True, 'id': '...', 'filename': 'test_policy.txt'}
✅ Document upload passed

[... more tests ...]

======================================================================
  INTEGRATION TESTS COMPLETED
======================================================================

✅ All integration tests passed!
```

### Frontend Tests

#### 3. Component Tests (`frontend/src/tests/*.test.jsx`)

React component tests using Vitest and React Testing Library.

**Test Coverage:**

- ✅ FileDrop component (file upload UI)
- ✅ ModelPicker component (LLM selector)
- ✅ MessageList component (chat history)
- ✅ ChatBox component (message input)

**Running Frontend Tests:**

```bash
cd frontend

# Install dependencies
npm install

# Run tests
npm test

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage
```

**Test Details:**

**FileDrop.test.jsx:**

- Renders upload area correctly
- Shows file input on click
- Accepts only PDF and TXT files
- Displays selected file name
- Handles drag and drop events

**ModelPicker.test.jsx:**

- Renders with default selection
- Displays all provider options (Ollama, OpenAI, Anthropic)
- Calls onChange when provider changes
- Updates model options based on provider

**MessageList.test.jsx:**

- Renders empty state with no messages
- Renders user and assistant messages
- Displays correct styling (blue for user, gray for assistant)
- Renders multiple messages in order
- Auto-scrolls to bottom on new messages

**ChatBox.test.jsx:**

- Renders input field and send button
- Allows typing in input field
- Calls onSend on button click
- Calls onSend on Enter key press
- Clears input after sending
- Does not send empty messages
- Disables correctly when disabled prop is true

## Test Fixtures and Mocks

### Backend Test Fixtures

Located in `backend/tests/run_tests.py`:

- In-memory SQLite database
- Mock configuration objects
- Sample text for chunking tests
- Sample schema data for validation

### Frontend Test Utilities

Located in `frontend/src/tests/setup.js`:

- React Testing Library cleanup
- Jest-DOM matchers
- QueryClient test wrapper
- Mock API responses

## Continuous Integration

### GitHub Actions Workflow (Optional)

Create `.github/workflows/tests.yml`:

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
          python-version: "3.11"
      - run: cd backend && pip install -r requirements.txt
      - run: cd backend && python tests/run_tests.py

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: "18"
      - run: cd frontend && npm install
      - run: cd frontend && npm test
```

## Test Data

### Sample Documents

For testing document upload and RAG pipeline:

**test_policy.txt:**

```
Company Leave Policy

1. Annual Leave
All employees are entitled to 20 days of paid annual leave per year.
Leave must be approved by your direct manager at least 2 weeks in advance.

2. Sick Leave
Employees receive 10 days of paid sick leave annually.
Medical certificates are required for absences exceeding 3 consecutive days.

3. Work From Home
Employees may work from home up to 2 days per week with manager approval.
Remote work must be requested 24 hours in advance via the HR portal.
```

**test_code_of_conduct.pdf:**
Create a PDF with similar content about company policies.

## Troubleshooting

### Common Issues

**1. Database Connection Errors**

```
psycopg2.OperationalError: could not connect to server
```

**Solution:** Ensure PostgreSQL is running:

```bash
docker-compose up -d postgres
```

**2. Ollama Connection Errors**

```
httpx.ConnectError: [Errno 111] Connection refused
```

**Solution:** Start Ollama and pull the model:

```bash
ollama serve
ollama pull llama3.1
```

**3. Pinecone Index Not Found**

```
pinecone.exceptions.NotFoundException: Index not found
```

**Solution:** Check your Pinecone API key and create the index:

```python
from pinecone import Pinecone
pc = Pinecone(api_key="your-key")
pc.create_index(
    name="policy-rag-index",
    dimension=768,
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-west-2")
)
```

**4. Frontend Test Errors**

```
Cannot find module '@testing-library/react'
```

**Solution:** Install test dependencies:

```bash
cd frontend
npm install
```

**5. Import Errors in Backend Tests**

```
ModuleNotFoundError: No module named 'langchain'
```

**Solution:** Install backend dependencies:

```bash
cd backend
pip install -r requirements.txt
```

## Test Coverage Goals

### Current Coverage

- Backend Core: ~85%
- Backend API: ~70%
- Frontend Components: ~75%
- Integration: ~60%

### Coverage Goals

- Backend Core: 95%
- Backend API: 90%
- Frontend Components: 90%
- Integration: 80%

## Adding New Tests

### Backend Test Example

```python
# tests/test_new_feature.py
def test_new_feature():
    """Test description."""
    # Arrange
    test_data = {"key": "value"}

    # Act
    result = new_feature(test_data)

    # Assert
    assert result is not None
    assert result["status"] == "success"
```

### Frontend Test Example

```jsx
// src/tests/NewComponent.test.jsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import NewComponent from "../components/NewComponent";

describe("NewComponent", () => {
  it("renders correctly", () => {
    render(<NewComponent />);
    expect(screen.getByText(/expected text/i)).toBeInTheDocument();
  });
});
```

## Performance Testing

### Load Testing with Locust (Optional)

Create `backend/tests/locustfile.py`:

```python
from locust import HttpUser, task, between

class RAGUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def chat_query(self):
        self.client.post("/api/chat", json={
            "question": "What is the leave policy?",
            "provider": "ollama",
            "model": "llama3.1",
            "user_id": "test-user"
        })

    @task(2)
    def list_documents(self):
        self.client.get("/api/documents/")
```

Run: `locust -f tests/locustfile.py --host http://localhost:8000`

## Security Testing

### OWASP ZAP Scanning (Optional)

```bash
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t http://localhost:8000 \
  -r zap_report.html
```

## Monitoring Test Results

### Test Result Artifacts

- Unit test logs: `backend/tests/logs/unit_tests.log`
- Integration test logs: `backend/tests/logs/integration_tests.log`
- Frontend coverage: `frontend/coverage/index.html`

## Best Practices

1. **Write tests first (TDD)** when adding new features
2. **Keep tests isolated** - no dependencies between tests
3. **Use meaningful test names** - describe what is being tested
4. **Mock external services** in unit tests
5. **Test edge cases** - empty inputs, null values, errors
6. **Maintain test data** - keep sample documents up to date
7. **Run tests before committing** - ensure nothing breaks
8. **Update tests with code changes** - keep tests in sync

## Next Steps

1. Add E2E tests with Playwright or Cypress
2. Implement visual regression testing
3. Add performance benchmarks
4. Set up automated test runs in CI/CD
5. Create test data generators for complex scenarios
6. Add accessibility testing (WCAG compliance)
7. Implement contract testing for API endpoints

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Testing Best Practices](https://testingjavascript.com/)
