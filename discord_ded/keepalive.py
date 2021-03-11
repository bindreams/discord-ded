"""Keep the bot alive when launching it on Repl.it"""
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def root():
    return "alive"

def run_server():
    app.run(host='0.0.0.0', port=8080)

def keepalive():
    """Start a server in background to keep the bot alive."""
    server = Thread(target=run_server)
    server.start()
