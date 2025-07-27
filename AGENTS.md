## AGENTS.md

This file provides guidelines for agentic coding assistants working in this repository.

### Build, Lint, and Test

- **No build step required** for this pure Python project.
- **Linting:** Use `flake8` or `pylint` for checking code quality.
  - `flake8 PCBDelayCalc.py`
  - `pylint PCBDelayCalc.py`
- **Testing:** Use `pytest`. Create tests in a `tests/` directory.
  - `pytest`
  - To run a single test file: `pytest tests/test_your_feature.py`

### Code Style Guidelines

- **Formatting:** Adhere to PEP 8. Use `black` or `autopep8` to format code.
  - `black .`
- **Imports:** Place all imports at the top of the file, grouped by standard library, third-party, and local modules.
- **Types:** Use type hints for all function signatures and variables. Run `mypy` to check types.
  - `mypy .`
- **Naming Conventions:**
  - `snake_case` for functions, methods, and variables.
  - `PascalCase` for classes.
  - `UPPER_SNAKE_CASE` for constants.
- **Error Handling:** Raise specific exceptions (`ValueError`, `TypeError`) instead of generic `Exception`.
- **Docstrings:** Write clear docstrings for all public classes, methods, and functions, following Google-style or reStructuredText format.
