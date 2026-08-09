# Contributing to SSH Tools Suite

Thank you for your interest in contributing to SSH Tools Suite! This document provides guidelines and information for contributors.

## 🤝 Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- A GitHub account

### Development Setup

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/NicholasKozma/ssh_tools_suite.git
   cd ssh_tools_suite
   ```

3. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

4. **Install development dependencies**:
   ```bash
   pip install -e .[dev,gui,rtsp]
   ```

5. **Create a new branch** for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 📋 How to Contribute

### Reporting Bugs

1. **Check existing issues** first to avoid duplicates
2. **Use the bug report template** when creating new issues
3. **Include detailed information**:
   - Python version
   - Operating system
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages and logs

### Suggesting Features

1. **Check existing feature requests** first
2. **Use the feature request template**
3. **Provide clear use cases** and benefits
4. **Consider implementation complexity**

### Contributing Code

1. **Follow the development setup** above
2. **Write tests** for new functionality
3. **Follow coding standards** (see below)
4. **Update documentation** as needed
5. **Submit a pull request**

## 🔧 Development Guidelines

### Coding Standards

- **Follow PEP 8** for Python code style
- **Use type hints** for function parameters and return values
- **Write docstrings** for all public functions and classes
- **Keep functions small** and focused on a single responsibility
- **Use meaningful variable names**

### Code Formatting

We use the following tools for code formatting and linting:

```bash
# Format code with black
black src/ tests/

# Check code style with flake8
flake8 src/ tests/

# Type checking with mypy
mypy src/
```

### Testing

- **Write tests** for all new functionality
- **Maintain test coverage** above 80%
- **Use pytest** for testing framework
- **Follow naming convention**: `test_*.py` for test files

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/gui/
```

### Documentation

- **Update README.md** for significant changes
- **Add docstrings** to all public APIs
- **Update MkDocs** documentation in `docs/`
- **Include examples** for new features

## 📝 Pull Request Process

1. **Create a descriptive PR title**:
   - `feat: add new tunnel auto-reconnection feature`
   - `fix: resolve RTSP connection timeout issue`
   - `docs: update installation instructions`

2. **Fill out the PR template** completely

3. **Ensure all checks pass**:
   - Tests pass
   - Code coverage maintained
   - No linting errors
   - Documentation builds successfully

4. **Request review** from maintainers

5. **Address feedback** promptly and professionally

## 🏗️ Project Structure

```
ssh-tools-suite/
├── src/                          # Source code
│   ├── ssh_tunnel_manager/       # Tunnel manager package
│   └── ssh_installer/            # SSH installer package
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── gui/                      # GUI tests
├── docs/                         # Documentation
├── tools/                        # Development tools
├── licenses/                     # Third-party licenses
├── ssh_tunnel_manager_app.py     # Main tunnel manager app
├── third_party_installer_app.py  # Main installer app
├── pyproject.toml                # Package configuration
├── requirements.txt              # Dependencies
├── pytest.ini                    # Test configuration
└── mkdocs.yml                   # Documentation configuration
```

## 🧪 Testing Guidelines

### Unit Tests
- Test individual functions and classes
- Mock external dependencies
- Focus on edge cases and error conditions

### Integration Tests
- Test component interactions
- Use real but lightweight dependencies where possible
- Test common user workflows

### GUI Tests
- Test user interface functionality
- Mock heavy operations
- Focus on user interaction flows

## 📚 Documentation

### Code Documentation
- **Docstrings**: Use Google-style docstrings
- **Type hints**: Include for all public APIs
- **Comments**: Explain complex logic, not obvious code

### User Documentation
- **Getting started guide**: For new users
- **API reference**: For developers
- **Troubleshooting**: Common issues and solutions
- **Examples**: Real-world use cases

## 🔍 Review Process

### What We Look For
- **Functionality**: Does it work as intended?
- **Code quality**: Is it well-written and maintainable?
- **Tests**: Are there adequate tests?
- **Documentation**: Is it properly documented?
- **Performance**: Does it impact performance negatively?
- **Security**: Are there any security concerns?

### Review Timeline
- **Initial response**: Within 2-3 business days
- **Full review**: Within 1 week for small changes
- **Complex changes**: May take longer, we'll communicate timelines

## 🎯 Priority Areas

We're particularly interested in contributions to:

1. **Cross-platform compatibility** improvements
2. **Performance optimizations**
3. **New tunnel types** and protocols
4. **Enhanced GUI features**
5. **Documentation and examples**
6. **Test coverage** improvements

## 💡 Tips for Contributors

- **Start small**: Begin with bug fixes or documentation improvements
- **Ask questions**: Don't hesitate to ask for clarification
- **Be patient**: Code review takes time, especially for complex changes
- **Stay updated**: Pull from main branch regularly to avoid conflicts
- **Test thoroughly**: Test your changes on multiple platforms if possible

## 📞 Getting Help

- **GitHub Discussions**: For general questions and ideas
- **GitHub Issues**: For bug reports and feature requests
- **Code review comments**: For specific implementation questions

## 🏆 Recognition

Contributors will be recognized in:
- **CONTRIBUTORS.md** file
- **Release notes** for significant contributions
- **README.md** acknowledgments section

Thank you for contributing to SSH Tools Suite! 🚀
