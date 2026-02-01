# Contributing to IWP Laser Visualizer

Thank you for your interest in contributing to the IWP Laser Visualizer! This document provides guidelines for contributing to the project.

## Code Standards

### Python Style
- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Include comprehensive docstrings for all classes and functions
- Maximum line length: 100 characters

### Documentation
- All public methods must have docstrings
- Include parameter types and descriptions
- Provide usage examples for complex functions
- Update README.md for new features

### Error Handling
- Use proper exception handling with specific exception types
- Log errors appropriately using the logging module
- Provide meaningful error messages
- Fail gracefully without crashing the visualizer

## Testing

### Manual Testing
- Test all IWP command types (TYPE_0-3)
- Verify network discovery functionality
- Test with various ILDA files
- Check performance with high packet rates

### Code Quality
- Ensure all imports are used
- Remove debug print statements
- Use logging instead of print for status messages
- Verify type hints with mypy when possible

## Submission Guidelines

### Pull Requests
- Create descriptive commit messages
- Include tests for new functionality
- Update documentation as needed
- Ensure compatibility with Python 3.8+

### Issues
- Provide clear reproduction steps
- Include system information (OS, Python version)
- Attach relevant log output
- Describe expected vs actual behavior

## Architecture Guidelines

### Module Structure
- Keep modules focused on single responsibilities
- Use clear, descriptive names for classes and functions
- Maintain consistent interfaces across modules
- Minimize dependencies between modules

### Performance Considerations
- Optimize for real-time performance
- Use efficient data structures
- Minimize memory allocations in hot paths
- Profile code for performance bottlenecks

## IWP Protocol Compatibility

When making changes to protocol handling:
- Maintain compatibility with IWPServer.cpp
- Support all existing IWP command types
- Preserve big-endian byte order
- Test with iwp-ilda.py sender

## Getting Started

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

For questions or discussions, please open an issue on the project repository.