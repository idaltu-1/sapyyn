# Contributing to Sapyyn Patient Referral System

Thank you for your interest in contributing to Sapyyn! This document provides guidelines for contributing to the project.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please treat all contributors with respect and professionalism.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/sapyyn-website.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Commit your changes: `git commit -m "Add feature: description"`
6. Push to your fork: `git push origin feature/your-feature-name`
7. Create a Pull Request

## Development Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

3. Start development server:
   ```bash
   npm run dev
   ```

## Coding Standards

### JavaScript/React
- Use ES6+ features
- Follow the ESLint configuration
- Use functional components with hooks
- Keep components small and focused
- Write meaningful variable and function names

### CSS
- Use CSS modules when possible
- Follow BEM naming convention for global styles
- Keep styles scoped to components

### Git Commits
- Use clear, descriptive commit messages
- Start with a verb (Add, Fix, Update, Remove, etc.)
- Keep commits focused on a single change
- Reference issue numbers when applicable

Example:
```
Fix: Resolve file upload error for large PDFs (#123)
```

## Testing

- Write tests for new features
- Ensure all tests pass before submitting PR
- Aim for >80% code coverage

## Pull Request Process

1. Update the README.md with details of changes if needed
2. Update documentation for API changes
3. Ensure CI/CD pipeline passes
4. Request review from maintainers
5. Address review feedback promptly

## Security

- Never commit sensitive data (API keys, passwords, etc.)
- Report security vulnerabilities privately to the maintainers
- Follow OWASP guidelines for web security
- Ensure HIPAA compliance for all patient data handling

## Questions?

Feel free to open an issue for any questions or concerns about contributing.