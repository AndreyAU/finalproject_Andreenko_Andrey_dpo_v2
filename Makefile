PYTHON=python3

.PHONY: install project build publish package-install lint

install:
	@echo "No installation required (standard library only)"

project:
	$(PYTHON) -m valutatrade_hub.cli.interface

lint:
	$(PYTHON) -m py_compile $(shell find valutatrade_hub -name "*.py")

build:
	mkdir -p dist
	cp README.md dist/README.md 2>/dev/null || true

publish:
	@echo "Publish step (dry run)"

package-install:
	@echo "Package install step not required"

