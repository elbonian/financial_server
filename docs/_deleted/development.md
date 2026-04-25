# Development Guide

## Setup Development Environment

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd financial_server
   ```

2. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Project Structure

```
financial_server/
├── docs/               # Documentation
├── scripts/            # Utility scripts
├── src/               # Core library code
│   └── financial_server/
│       ├── main.py    # FastAPI application
│       ├── data_fetcher.py
│       ├── database.py
│       ├── models.py
│       └── utils.py
└── tests/             # Test suite
```

## Running Tests

### All Tests
```bash
pytest tests/
```

### Specific Test File
```bash
pytest tests/test_api.py
```

### With Coverage
```bash
pytest --cov=src/financial_server tests/
```

## Code Style

We follow PEP 8 with these additions:
- Line length: 88 characters (Black default)
- Docstrings: Google style
- Type hints: Required for public functions

Example:
```python
def calculate_date_range(
    start_date: date,
    end_date: date
) -> List[date]:
    """Calculate business days between dates.

    Args:
        start_date: Start date
        end_date: End date

    Returns:
        List of dates excluding weekends
    """
    ...
```

## Git Workflow

1. Create feature branch:
   ```bash
   git checkout -b feature/new-feature
   ```

2. Make changes and commit:
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

3. Run tests:
   ```bash
   pytest tests/
   ```

4. Push changes:
   ```bash
   git push origin feature/new-feature
   ```

## Adding Features

1. Update requirements if needed:
   ```python
   # setup.py
   setup(
       ...
       install_requires=[
           "new-package>=1.0.0",
       ],
   )
   ```

2. Add tests first:
   ```python
   # tests/test_new_feature.py
   def test_new_feature():
       result = new_feature()
       assert result == expected
   ```

3. Implement feature:
   ```python
   # src/financial_server/new_feature.py
   def new_feature():
       return expected
   ```

4. Update documentation:
   - Add to relevant .md files
   - Update API docs if needed
   - Add usage examples

## Database Changes

1. Update schema in `database.py`:
   ```python
   def create_tables(self):
       self.cursor.execute("""
           CREATE TABLE IF NOT EXISTS new_table (
               id INTEGER PRIMARY KEY,
               ...
           )
       """)
   ```

2. Add migration script:
   ```python
   # scripts/migrations/001_add_new_table.py
   def upgrade():
       ...

   def downgrade():
       ...
   ```

## Debugging

1. Enable debug logging:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. Use FastAPI debug mode:
   ```bash
   uvicorn main:app --reload --log-level debug
   ```

3. SQLite debugging:
   ```python
   self.cursor.execute("EXPLAIN QUERY PLAN SELECT ...")
   ```

## Performance Testing

1. Run benchmark tests:
   ```bash
   pytest tests/test_performance.py -v
   ```

2. Profile code:
   ```python
   import cProfile
   cProfile.run('function_to_profile()')
   ```

## Documentation

1. Generate API docs:
   ```bash
   python scripts/generate_docs.py
   ```

2. Update examples:
   ```bash
   python scripts/update_examples.py
   ```

## Release Process

1. Update version:
   ```python
   # setup.py
   setup(
       version="1.1.0",
       ...
   )
   ```

2. Update changelog:
   ```markdown
   # CHANGELOG.md
   ## [1.1.0] - 2025-08-03
   - Added new feature
   - Fixed bug
   ```

3. Create release:
   ```bash
   git tag v1.1.0
   git push origin v1.1.0
   ```