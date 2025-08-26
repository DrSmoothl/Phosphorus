# Phosphorus - JPlag based Plagiarism Checker Server for Hydro

A FastAPI-based server that wraps JPlag command-line tool for plagiarism detection in Hydro OJ, with an integrated frontend plugin for seamless OJ integration.

## Features

- **Backend API**: RESTful API for plagiarism detection using JPlag
- **Hydro OJ Integration**: Direct integration with Hydro OJ MongoDB database
- **Frontend Plugin**: Ready-to-use Hydro OJ plugin for web interface
- **Multi-language Support**: Supports C++, Java, Python, JavaScript, and more
- **Real-time Analysis**: Live progress and detailed similarity reports
- **Clustering Detection**: Automatic grouping of similar submissions

## Components

### 1. Phosphorus Backend (`src/`)
FastAPI server providing plagiarism detection services:
- Contest submission analysis
- JPlag integration
- MongoDB data persistence
- RESTful API endpoints

### 2. Hydro OJ Plugin (`FrontendHydroPlugin/`)
Complete frontend plugin for Hydro OJ:
- TypeScript handlers for contest integration
- Jinja2 templates for user interface
- Multi-language support (English/Chinese)
- Administrative controls and permissions

## Quick Start

### Backend Setup

1. **Prerequisites**
   - Python 3.11+
   - uv (for dependency management)
   - Java 11+ (for JPlag)
   - MongoDB

### Installation

1. Clone the repository:
```bash
git clone https://github.com/DrSmoothl/Phosphorus
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

### Frontend Plugin Setup

The Hydro OJ plugin provides a complete web interface for plagiarism detection.

#### Quick Installation

1. **Automatic installation**:
   ```bash
   ./install_plugin.sh /path/to/hydro/addons
   ```

2. **Manual installation**:
   ```bash
   # Copy plugin to Hydro addons directory
   cp -r FrontendHydroPlugin /path/to/hydro/addons/CAUCOJ-Phosphorus
   
   # Install dependencies
   cd /path/to/hydro/addons/CAUCOJ-Phosphorus
   npm install
   
   # Configure backend URL
   cp .env.example .env
   # Edit .env to set PHOSPHORUS_URL=http://your-backend:8000
   ```

3. **Enable in Hydro OJ**:
   Add `CAUCOJ-Phosphorus` to your Hydro addons configuration and restart.

#### Usage

1. Navigate to any contest admin page in Hydro OJ
2. Click "Plagiarism Detection" in the admin menu
3. Configure analysis parameters and start detection
4. View detailed similarity reports and clusters

For detailed instructions, see [`FrontendHydroPlugin/README.md`](FrontendHydroPlugin/README.md).

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

[GPL v3.0](./LICENSE)
