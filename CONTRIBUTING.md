# Contributing to Reminder App

Thank you for your interest in contributing to Reminder App! We welcome contributions from the community.

## How to Contribute

1. Fork the repository
2. Create a new branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Test your changes
5. Submit a pull request

## Development Setup

1. **Prerequisites**
   - Python 3.8+
   - PostgreSQL
   - Redis
   - Git

2. **Local Development**
```bash
# Clone repository
git clone https://github.com/yourusername/reminder-app.git
cd reminder-app

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your settings

# Start services
redis-server
celery -A tasks.celery worker --loglevel=info
celery -A tasks.celery beat --loglevel=info
python app.py
```

## Code Style

- Follow PEP 8 guidelines
- Add comments for complex logic
- Write meaningful commit messages
- Use type hints
- Write docstrings
- Include tests

## Reporting Issues

- Use the GitHub issue tracker
- Include steps to reproduce
- Include expected vs actual behavior

## Pull Request Process
1. Update documentation
2. Add tests
3. Update CHANGELOG.md
4. Submit PR with description

## Production Considerations
- Test with PostgreSQL
- Verify Celery tasks
- Check Redis connection
- Test email functionality 