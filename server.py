"""TeknoMedis — Landing Page Server."""
import os
import re
from flask import Flask, send_from_directory, jsonify

app = Flask(__name__, static_folder='.', static_url_path='')

DOWNLOADS_DIR = os.path.join(os.path.dirname(__file__), 'downloads')

# Pattern: {ProductName}-v{X.Y.Z}.zip atau .exe (atau -{X.Y.Z} tanpa v)
_VERSION_RE = re.compile(r'^(.+?)-v?(\d+)\.(\d+)\.(\d+)\.(zip|exe)$', re.IGNORECASE)


def _scan_downloads():
    """Return {product_code: {filename, version, url, size_mb}} — versi terbaru per produk."""
    products = {}
    if not os.path.isdir(DOWNLOADS_DIR):
        return products
    for fname in os.listdir(DOWNLOADS_DIR):
        m = _VERSION_RE.match(fname)
        if not m:
            continue
        name, maj, mnr, pt, ext = m.groups()
        version = (int(maj), int(mnr), int(pt))
        # Normalize product name → code
        code = name.lower().replace('-pro', '').replace(' ', '').replace('_', '')
        if code.startswith('teknomedis'):
            code = code.replace('teknomedishubsetup', 'hub').replace('teknomedishub', 'hub').replace('teknomedis', 'hub')
        full_path = os.path.join(DOWNLOADS_DIR, fname)
        size = os.path.getsize(full_path)
        entry = {
            'filename': fname,
            'version': f'{maj}.{mnr}.{pt}',
            'version_tuple': version,
            'url': f'/downloads/{fname}',
            'size_mb': round(size / 1024 / 1024, 2),
            'ext': ext.lower(),
        }
        existing = products.get(code)
        if not existing or version > existing.get('version_tuple', (0, 0, 0)):
            products[code] = entry
    for v in products.values():
        v.pop('version_tuple', None)
    return products


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/downloads.json')
def api_downloads():
    """Return latest version per product (scan folder /downloads/).
    Landing page pake ini untuk dynamic download button."""
    return jsonify({'ok': True, 'products': _scan_downloads()})


@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8888))
    print(f"\n  TeknoMedis — Landing Page")
    print(f"  http://0.0.0.0:{port}\n")
    app.run(host='0.0.0.0', port=port, debug=False)
