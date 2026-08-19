import threading
import webview

from main import app


def run_server():
    app.run(port=5000, use_reloader=False)


if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    webview.create_window("Transcript Deck", "http://127.0.0.1:5000", width=720, height=760, min_size=(480, 560))
    webview.start()
