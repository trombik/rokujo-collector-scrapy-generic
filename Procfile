proxy: env PYTHONUNBUFFERED=1 pproxy -r socks://127.0.0.1:9050
analyzer: cd vendor/rokujo-analyzer && uv run gunicorn main:app -c gunicorn_config.py
