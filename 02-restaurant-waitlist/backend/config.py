import os

DEFAULT_PORT = int(os.environ.get("PORT", "8091"))

# Origins allowed to call this API from a browser (CORS). Defaults cover the
# frontend dev server, which the @lovable.dev/vite-tanstack-config Vite plugin
# pins to port 8080 (see frontend/vite.config.ts). Override with a
# comma-separated ALLOWED_ORIGINS env var for other local setups.
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "ALLOWED_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080"
    ).split(",")
    if origin.strip()
]
