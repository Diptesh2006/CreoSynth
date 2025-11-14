#!/bin/bash
# Clean up unnecessary files from installed packages to reduce size
echo "Cleaning up installed packages..."

# Remove test files and directories
find . -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "test" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*_test.py" -delete 2>/dev/null || true
find . -type f -name "*_tests.py" -delete 2>/dev/null || true
find . -type f -name "test_*.py" -delete 2>/dev/null || true

# Remove example and demo directories
find . -type d -name "examples" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "example" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "demos" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "demo" -exec rm -rf {} + 2>/dev/null || true

# Remove documentation
find . -type f -name "*.md" -delete 2>/dev/null || true
find . -type d -name "docs" -exec rm -rf {} + 2>/dev/null || true

# Remove Jupyter notebooks
find . -type f -name "*.ipynb" -delete 2>/dev/null || true
find . -type d -name ".ipynb_checkpoints" -exec rm -rf {} + 2>/dev/null || true

# Remove __pycache__ directories
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true

echo "Cleanup complete!"

