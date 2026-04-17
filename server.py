"""TeknoMedis — Landing Page Server."""
from flask import Flask, send_from_directory
import os

app = Flask(__name__, static_folder='.', static_url_path='')

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8888))
    print(f"\n  TeknoMedis — Landing Page")
    print(f"  http://0.0.0.0:{port}\n")
    app.run(host='0.0.0.0', port=port, debug=False)
