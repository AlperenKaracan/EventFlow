import os

from app.server import run_server

if __name__ == "__main__":
    run_server(
        app_import="tests.support.graceful_app:app",
        host=os.environ.get("GRACEFUL_TEST_HOST", "127.0.0.1"),
        port=int(os.environ["GRACEFUL_TEST_PORT"]),
    )
