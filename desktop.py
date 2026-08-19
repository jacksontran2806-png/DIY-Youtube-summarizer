import socket
import threading

import webview

from main import app


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def run_server(port: int):
    app.run(port=port, use_reloader=False)


if __name__ == "__main__":
    port = find_free_port()
    threading.Thread(target=run_server, args=(port,), daemon=True).start()
    webview.create_window(
        "Transcript Deck",
        f"http://127.0.0.1:{port}",
        width=720, height=760, min_size=(480, 560),
    )
    webview.start()
