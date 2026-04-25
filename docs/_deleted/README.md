# Financial Data Server Documentation

Welcome to the Financial Data Server documentation! This server provides real-time financial data with intelligent caching through a RESTful API.

## Quick Links

- [Usage Guide](usage.md) - How to use the server
- [API Documentation](api.md) - API endpoints and examples
- [Real-World Examples](real_world_examples.md) - Actual usage examples with real data
- [Testing Guide](testing.md) - Comprehensive test suite documentation
- [Architecture](architecture.md) - System design and components
- [Development Guide](development.md) - Development setup and guidelines
- [Requirements](requirements.md) - Project requirements and features

## Overview

The Financial Data Server is a local server that provides:
- Real-time financial data
- Intelligent caching
- RESTful API
- Support for stocks and cryptocurrencies

## Getting Started

1. Installation:
   ```bash
   pip install -e .
   ```

2. Start the server:
   ```bash
   python scripts/server.py
   ```

3. Get some data:
   ```bash
   curl "http://localhost:8000/api/v1/tickers/BTC-USD/prices?start_date=2024-01-01&end_date=2024-12-31"
   ```

## Documentation Structure

- `usage.md` - Detailed usage examples and best practices
- `api.md` - Complete API documentation
- `architecture.md` - System design and components
- `development.md` - Development setup and guidelines
- `requirements.md` - Project requirements and features

## Contributing

See the [Development Guide](development.md) for:
- Setting up your development environment
- Running tests
- Code style guidelines
- Git workflow

## Support

For issues and questions:
1. Check the documentation
2. Run server health check
3. Check the logs
4. Run tests

## License

MIT License - See LICENSE file for details