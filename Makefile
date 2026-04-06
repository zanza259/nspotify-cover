.PHONY: help build clean install install-dev dist

help:
	@echo "ncspot-cover build targets:"
	@echo ""
	@echo "  make build          Build standalone executable with PyInstaller"
	@echo "  make clean          Remove build artifacts and dist directory"
	@echo "  make install        Install package in current environment"
	@echo "  make install-dev    Install package in development mode"
	@echo "  make dist           Build distribution package (wheel/tarball)"
	@echo "  make help           Show this help message"

build:
	@echo "Building ncspot-cover executable..."
	uv run PyInstaller ncspot-cover.spec
	@echo ""
	@if [ -f dist/ncspot-cover ] || [ -f dist/ncspot-cover.exe ]; then \
		echo "✓ Build successful!"; \
		echo "Executable location: ./dist/ncspot-cover"; \
		echo ""; \
		echo "Note: This executable requires ncspot and jp2a to be installed"; \
		echo "and available in your system PATH."; \
	else \
		echo "✗ Build completed but executable not found"; \
		exit 1; \
	fi

clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/ dist/ *.egg-info .eggs __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -f ncspot-cover.spec.bak
	@echo "✓ Clean complete"

install:
	uv pip install .

install-dev:
	uv sync

dist:
	uv run python -m build
