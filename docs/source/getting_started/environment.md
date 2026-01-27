# Understanding Environment

The project is packaged with `uv`, a Python package and project manager, written in Rust.
The spiders are written in Python with a scraping library, `scrapy`.

## Running Commands

`uv` installs required libraries and commands, including `scrapy`.
To run commands in `uv` environment, prefix commands with `uv run`.
The following command runs installed `scrapy` and displays its version.

```console
uv run scrapy --version
```

The `uv run` is almost always necessary to run commands in the project.
