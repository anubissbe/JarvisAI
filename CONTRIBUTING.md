# Contributing to JarvisAI

Thank you for your interest in contributing to JarvisAI! This guide will help you get started with contributing to our project.

## > Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:

- **Be respectful**: Treat everyone with respect and kindness
- **Be inclusive**: Welcome newcomers and help them succeed
- **Be collaborative**: Work together to improve the project
- **Be constructive**: Provide helpful feedback and suggestions

## =€ Getting Started

### Prerequisites

Before contributing, ensure you have:

- Git installed and configured
- Docker and Docker Compose
- Node.js 18+ for frontend development
- Python 3.11+ for backend development
- Access to NVIDIA GPUs (for testing GPU features)

### Setting Up Development Environment

1. **Fork the repository**
   ```bash
   # Fork the repo on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/JarvisAI.git
   cd JarvisAI
   ```

2. **Set up the development environment**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Start development services
   docker-compose -f docker-compose.dev.yml up -d
   
   # Install dependencies
   npm install                              # Frontend
   pip install -r backend/requirements.txt  # Backend
   ```

3. **Run tests to ensure everything works**
   ```bash
   # Backend tests
   cd backend && python -m pytest
   
   # Frontend tests
   npm test
   ```

## =Ý How to Contribute

### Reporting Issues

Before creating an issue, please:

1. **Search existing issues** to avoid duplicates
2. **Use the issue template** when creating new issues
3. **Provide detailed information**:
   - Steps to reproduce
   - Expected vs actual behavior
   - System information (OS, Docker version, GPU specs)
   - Relevant logs or error messages

### Submitting Pull Requests

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow our coding standards (see below)
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
   ```bash
   # Run all tests
   npm run test:all
   
   # Check code quality
   npm run lint
   npm run typecheck
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add amazing new feature"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   # Then create a pull request on GitHub
   ```

## =' Development Guidelines

### Code Style

#### Python (Backend)
- Follow **PEP 8** style guide
- Use **type hints** for all functions
- Maximum line length: **88 characters**
- Use **Black** for formatting
- Use **isort** for import ordering

```python
# Good example
async def process_document(
    document_id: str, 
    user_id: str, 
    options: ProcessingOptions
) -> DocumentResult:
    """Process a document with the given options."""
    try:
        result = await document_processor.process(document_id, options)
        return result
    except ProcessingError as e:
        logger.error(f"Failed to process document {document_id}: {e}")
        raise
```

#### TypeScript/React (Frontend)
- Use **TypeScript** for all code
- Follow **Prettier** formatting
- Use **ESLint** rules
- Prefer **functional components** with hooks
- Use **Tailwind CSS** for styling

```typescript
// Good example
interface ChatMessageProps {
  message: Message;
  onReply: (content: string) => void;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ 
  message, 
  onReply 
}) => {
  return (
    <div className="flex flex-col space-y-2 p-4">
      <div className="text-sm text-gray-600">{message.timestamp}</div>
      <div className="text-base">{message.content}</div>
    </div>
  );
};
```

### Testing Guidelines

#### Backend Testing
- Use **pytest** for all tests
- Aim for **80%+ code coverage**
- Write **unit tests** for individual functions
- Write **integration tests** for API endpoints
- Use **fixtures** for test data

```python
# Example test
import pytest
from fastapi.testclient import TestClient

def test_chat_endpoint(client: TestClient, auth_headers):
    response = client.post(
        "/api/v1/chat",
        json={"message": "Hello", "user_id": "test"},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert "response" in response.json()
```

#### Frontend Testing
- Use **Jest** and **React Testing Library**
- Write **component tests**
- Test **user interactions**
- Mock **external dependencies**

```typescript
// Example test
import { render, screen, fireEvent } from '@testing-library/react';
import { ChatMessage } from './ChatMessage';

test('calls onReply when reply button is clicked', () => {
  const mockOnReply = jest.fn();
  const message = { id: '1', content: 'Hello', timestamp: '2025-01-01' };
  
  render(<ChatMessage message={message} onReply={mockOnReply} />);
  
  fireEvent.click(screen.getByText('Reply'));
  expect(mockOnReply).toHaveBeenCalled();
});
```

### Documentation

- Update **README.md** for user-facing changes
- Update **API documentation** for backend changes
- Add **JSDoc comments** for complex functions
- Update **architecture docs** for significant changes

### Git Commit Guidelines

Use **Conventional Commits** format:

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(chat): add therapeutic mode support
fix(auth): resolve OAuth 2.1 token refresh issue
docs(api): update authentication endpoint documentation
```

## = Code Review Process

1. **All PRs require review** before merging
2. **CI/CD checks must pass**:
   - All tests passing
   - Code quality checks
   - Security scans
   - Documentation builds

3. **Review criteria**:
   - Code follows style guidelines
   - Tests are comprehensive
   - Documentation is updated
   - No breaking changes (unless necessary)

4. **Addressing feedback**:
   - Respond to all review comments
   - Make requested changes promptly
   - Ask for clarification if needed

## <¯ Areas for Contribution

### High Priority
- **OAuth 2.1 implementation** improvements
- **Vector search optimization** with CAGRA
- **Therapeutic mode** enhancements
- **Multi-agent workflows** with LangGraph

### Medium Priority
- **Frontend UI/UX** improvements
- **Documentation** and tutorials
- **Testing** coverage improvements
- **Performance** optimizations

### Low Priority
- **Code refactoring**
- **Dependency updates**
- **Developer tooling** improvements

## = Security

If you discover a security vulnerability:

1. **Do NOT open a public issue**
2. **Email** the maintainers directly
3. **Include** detailed information about the vulnerability
4. **Wait** for confirmation before disclosing

## =Ú Resources

- **Architecture Guide**: [JARVIS_ARCHITECTURE_BLUEPRINT_2025.md](JARVIS_ARCHITECTURE_BLUEPRINT_2025.md)
- **Technology Validation**: [JARVIS_TECH_VALIDATION_2025.md](JARVIS_TECH_VALIDATION_2025.md)
- **API Documentation**: Available at `/docs` when running locally
- **Development Chat**: Join our development discussions

## S Getting Help

- **GitHub Discussions**: For general questions and discussions
- **GitHub Issues**: For bug reports and feature requests
- **Documentation**: Check our comprehensive guides first

## =O Recognition

Contributors will be:

- **Listed** in our contributors section
- **Mentioned** in release notes for significant contributions
- **Invited** to join the core team for exceptional contributions

Thank you for contributing to JarvisAI! >