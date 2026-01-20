.PHONY: docs gen-docs build-docs clean

docs: gen-docs build-docs

gen-docs:
	uv run sphinx-apidoc -f -o docs/source ./generic

build-docs:
	uv run sphinx-build -b html docs/source docs/build

clean:
	rm -rf docs/build
