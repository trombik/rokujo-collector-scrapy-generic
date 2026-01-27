.PHONY: docs build-docs clean

docs: build-docs

build-docs:
	uv run sphinx-build -b html docs/source docs/build

clean:
	rm -rf docs/build docs/source/apidocs
