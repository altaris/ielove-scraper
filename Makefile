DOCS_PATH 		= docs
SRC_PATH 		= ielove
VENV			= ./venv

.ONESHELL:

all: format typecheck lint

.PHONY: docs
docs:
	-@mkdir $(DOCS_PATH) > /dev/null 2>&1
	pdoc -d google --output-directory $(DOCS_PATH) $(SRC_PATH)

.PHONY: docs-browser
docs-browser:
	-@mkdir $(DOCS_PATH) > /dev/null 2>&1
	pdoc -d google $(SRC_PATH)

.PHONY: format
format:
	black --line-length 79 --target-version py310 $(SRC_PATH)

.PHONY: lint
lint:
	pylint $(SRC_PATH)

.PHONY: typecheck
typecheck:
	mypy -p $(SRC_PATH)
