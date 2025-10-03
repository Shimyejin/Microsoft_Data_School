import json
import time
import threading
import signal
import sys
from websocket import WebSocketApp

WS_URL = "wss://api.upbit.com/websocket/v1"
MARKETS = ["KRW-BTC", "KRW-ETH", "KRW-XRP"]

REQUEST_PAYLOAD = [
    {"ticket":"graceful"},
    {"type":"ticker","codes":MARKETS},
    {"format":"SIMPLE"}
]

stop_event = threading.Event()
ws_app_container = {"app": None}  # mutable container so handler can access current app

def on_message(ws, message):
    data = json.loads(message)
    print("recv:", data)

def on_error(ws, error):
    print("websocket error:", error)

def on_close(ws, close_status_code, close_msg):
    print("websocket closed", close_status_code, close_msg)

def on_open(ws):
    print("websocket opened - sending subscribe")
    ws.send(json.dumps(REQUEST_PAYLOAD))

def ws_worker():
    # reconnect loop, but respect stop_event
    backoff = 1
    while not stop_event.is_set():
        ws = WebSocketApp(
            WS_URL,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )
        ws_app_container["app"] = ws
        try:
            # run_forever blocks this worker thread until connection closes or ws.close() called
            ws.run_forever(ping_interval=20, ping_timeout=10)
        except Exception as e:
            print("run_forever exception:", e)
        finally:
            ws_app_container["app"] = None

        if stop_event.is_set():
            break  # exit reconnect loop

        # simple backoff before reconnecting (interruptible)
        print(f"connection lost — reconnecting in {backoff}s (or Ctrl+C to stop)...")
        for _ in range(int(backoff * 10)):
            if stop_event.is_set():
                break
            time.sleep(0.1)
        backoff = min(backoff * 2, 60)

def signal_handler(sig, frame):
    # called in main thread on Ctrl+C
    print("\nSIGINT received — shutting down...")
    stop_event.set()
    app = ws_app_container.get("app")
    if app:
        try:
            app.close()  # this will make run_forever() return in worker thread
        except Exception as e:
            print("error while closing ws:", e)

def main():
    # register handler in main thread (Windows: must be in main thread)
    signal.signal(signal.SIGINT, signal_handler)

    t = threading.Thread(target=ws_worker, daemon=True)
    t.start()

    # main thread waits until worker finishes or stop_event set
    try:
        while t.is_alive():
            t.join(timeout=1)
    except KeyboardInterrupt:
        # fallback if signal somehow didn't trigger handler
        signal_handler(None, None)

    print("worker finished, exiting program.")

if __name__ == "__main__":
    main()