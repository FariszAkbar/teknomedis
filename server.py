"""TeknoMedis — Landing Page Server."""
import os
import re
import time
import json as _json
import urllib.request as _urlreq
from flask import Flask, send_from_directory, jsonify

LICENSE_SERVER = os.environ.get('LICENSE_SERVER', 'http://localhost:8061')
_PRICING_CACHE = {'data': None, 'fetched_at': 0}
_PRICING_CACHE_TTL = 60  # detik — biar landing gak hammer license-server

app = Flask(__name__, static_folder='.', static_url_path='')

DOWNLOADS_DIR = os.path.join(os.path.dirname(__file__), 'downloads')

# Pattern: {ProductName}-v{X.Y.Z}.zip / .exe / .apk (atau -{X.Y.Z} tanpa v)
_VERSION_RE = re.compile(r'^(.+?)-v?(\d+)\.(\d+)\.(\d+)\.(zip|exe|apk)$', re.IGNORECASE)


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
        # Normalize product name → code (lowercase, strip separators/suffixes)
        code = name.lower().replace('-pro', '').replace('-', '').replace(' ', '').replace('_', '')
        if code.startswith('teknomedis'):
            code = code.replace('teknomedishubsetup', 'hub').replace('teknomedishub', 'hub').replace('teknomedis', 'hub')
        # Normalize "<product>setup" -> "<product>" (Inno Setup .exe naming).
        # Contoh: CaseMixProSetup -> casemixprosetup -> casemix
        if code.endswith('setup'):
            code = code[:-5]  # strip 'setup'
        if code == 'casemixpro':
            code = 'casemix'
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
        # Prefer higher version; kalau version sama prefer .exe (complete installer)
        # over .zip (app code only, butuh Python pre-installed).
        ext_priority = {'exe': 3, 'apk': 2, 'zip': 1}
        should_replace = False
        if not existing:
            should_replace = True
        elif version > existing.get('version_tuple', (0, 0, 0)):
            should_replace = True
        elif (version == existing.get('version_tuple')
                and ext_priority.get(ext.lower(), 0) > ext_priority.get(existing.get('ext', ''), 0)):
            should_replace = True
        if should_replace:
            products[code] = entry
    for v in products.values():
        v.pop('version_tuple', None)
    return products


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/api/license-catalog')
def api_license_catalog():
    """Proxy ke license-server /api/catalog. Cache 60 detik biar gak hammer.

    Single source of truth pricing — admin ubah harga di license-server panel
    -> landing auto-update tanpa redeploy.
    """
    now = time.time()
    if _PRICING_CACHE['data'] and (now - _PRICING_CACHE['fetched_at']) < _PRICING_CACHE_TTL:
        return jsonify(_PRICING_CACHE['data'])
    try:
        with _urlreq.urlopen(f'{LICENSE_SERVER}/api/catalog', timeout=5) as resp:
            data = _json.loads(resp.read())
        _PRICING_CACHE['data'] = data
        _PRICING_CACHE['fetched_at'] = now
        return jsonify(data)
    except Exception as e:
        # Kalau license-server down, return cache lama (kalau ada) atau error
        if _PRICING_CACHE['data']:
            return jsonify(_PRICING_CACHE['data'])
        return jsonify({'ok': False, 'error': f'License server unreachable: {e}'}), 502


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
