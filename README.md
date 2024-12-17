# TheLifeCarePlanner

A Django-based application for creating and managing life care plans.

## Development Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd lifecare_project
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install development dependencies:
```bash
pip install pre-commit black flake8 flake8-django isort mypy django-stubs pytest pytest-django pytest-cov
```

5. Set up pre-commit hooks:
```bash
pre-commit install
```

6. Run migrations:
```bash
python manage.py migrate
```

7. Run tests:
```bash
pytest
```

## Development Guidelines

### Code Quality

- All code must pass pre-commit hooks
- Maintain test coverage above 80%
- Follow Django's style guide
- Use type hints where possible
- Document all functions and classes

### Git Workflow

1. Create a feature branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make changes and commit:
```bash
git add .
git commit -m "Descriptive commit message"
```

3. Push changes:
```bash
git push origin feature/your-feature-name
```

4. Create a pull request

### Testing

- Write tests for all new features
- Run the full test suite before committing
- Include both unit and integration tests
- Test edge cases and error conditions

### Database Changes

- Always use migrations
- Back up data before major changes
- Test migrations thoroughly
- Document schema changes

### Security

- Never commit sensitive data
- Use environment variables for secrets
- Follow Django security best practices
- Regularly update dependencies

## Project Structure

```
lifecare_project/
├── plans/              # Life care plan management
├── core/              # Core functionality
├── codes/             # Procedure codes
├── geographic/        # Geographic data
├── security/         # Authentication and authorization
└── surgeries/        # Surgery-related functionality
```

## Deployment

- Follow the deployment checklist
- Use environment variables
- Run security checks
- Backup database before deploying
- Test in staging environment first

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and quality checks
5. Submit a pull request

## License

[Your License Here]
