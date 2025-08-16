# Phosphorus - JPlag based Plagiarism Checker Server for Hydro

A FastAPI-based server that wraps JPlag command-line tool for plagiarism detection in Hydro OJ.

## Development Setup

### Prerequisites
- Python 3.11+
- uv (for dependency management)

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd Phosphorus
```

2. Create virtual environment and install dependencies:
```bash
uv venv
uv pip install -e ".[dev]"
```

3. Activate virtual environment:
```bash
# Windows
.venv\Scripts\activate
# Unix/macOS
source .venv/bin/activate
```

### Development

#### Run the server:

Option 1 - Using the main script:
```bash
uv run python main.py
```

Option 2 - Using the console script:
```bash
uv run phosphorus
```

Option 3 - Using the development runner:
```bash
uv run python run_dev.py
```

#### Run tests:
```bash
uv run pytest
```

#### Code formatting and linting:
```bash
uv run ruff check .
uv run ruff format .
```

## Project Structure

```
/src                 # Main source code
  /api               # API route handlers
  /common            # Common modules (logger, config)
  /core              # Core business logic
  /utils             # Utility functions
/tests               # Unit tests
```

## API Documentation

Once the server is running, visit:
- Interactive API docs: http://localhost:8000/docs
- ReDoc documentation: http://localhost:8000/redoc

## License

[Your License Here]
