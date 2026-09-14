"""Password-protected synthetic judge sandbox. Warm-instance storage is temporary."""
import base64
import http.client
import os
import re
import threading
from pathlib import Path

_server = None


def inline_assets(html):
    """Deliver static assets together for the single-concurrency judge sandbox."""
    root = Path(__file__).parent / 'web'
    scripts = []
    def script(match):
        source = re.search(r'src="(/[^"]+)"', match[0]).group(1)
        scripts.append('<script>' + (root / source.lstrip('/')).read_text().replace('</script', '<\\/script') + '</script>')
        return ''
    html = re.sub(r'<script[^>]+src="/[^"]+"[^>]*></script>', script, html)
    html = re.sub(r'<link rel="stylesheet" href="(/[^"]+)">',
                  lambda m: '<style>' + (root / m[1].lstrip('/')).read_text() + '</style>', html)
    return html.replace('</body>', ''.join(scripts) + '</body>')


def response(code, body, headers=None):
    return {'statusCode': code, 'headers': {'Content-Type': 'text/plain; charset=utf-8',
            'Cache-Control': 'no-store', **(headers or {})}, 'body': body}


def local_server():
    global _server
    if _server is None:
        from invoice_store import Store
        from server import make_server
        folder = Path('/tmp/hotel-judge-sandbox')
        folder.mkdir(exist_ok=True)
        store = Store(folder / 'requests.sqlite')
        store.seed()
        _server = make_server(0, store,secure_cookies=True)
        _server.auth.set_password('judge',os.environ['JUDGE_PASSWORD'],'Judge')
        threading.Thread(target=_server.serve_forever, daemon=True).start()
    return _server


def handler(event, context):
    headers = {k.lower(): v for k, v in event.get('headers', {}).items()}
    if not os.environ.get('JUDGE_PASSWORD'):
        return response(503,'Judge access is not configured')
    domain = event.get('requestContext', {}).get('domainName', '')
    if not domain or headers.get('origin', 'https://' + domain) != 'https://' + domain:
        return response(403, 'Origin not allowed')
    method = event.get('requestContext', {}).get('http', {}).get('method', '')
    path = event.get('rawPath', '/')
    allowed = {'/', '/app.js', '/style.css', '/i18n.js', '/locales.js',
               '/login', '/login.js', '/login.css', '/healthz',
               '/api/auth/login', '/api/auth/logout', '/api/auth/session',
               '/vendor/i18next.min.js', '/api/health', '/api/requests',
               '/api/evidence', '/api/intake', '/api/action', '/api/details', '/api/sample-file',
               '/followup.js', '/api/followup', '/api/followup/confirm'}
    if path not in allowed or method not in {'GET', 'POST'}:
        return response(404, 'Not found')
    try:
        body = (base64.b64decode(event.get('body', ''), validate=True)
                if event.get('isBase64Encoded') else (event.get('body') or '').encode())
    except (ValueError, TypeError):
        return response(400, 'Invalid body')
    if len(body) > 20000:
        return response(413, 'Request too large')
    server = local_server()
    server.monitor.scan()
    connection=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=110)
    try:
        connection.request(method,path,body=body if method=='POST' else None,
            headers={'Content-Type':headers.get('content-type',''),
                     'Cookie':'; '.join(event.get('cookies',[])) or headers.get('cookie','')})
        upstream=connection.getresponse()
        data = upstream.read().decode('utf-8')
        result = response(upstream.status, data,
                          {'Content-Type': upstream.headers.get('Content-Type', 'text/plain')})
        for key in ('Location','X-Frame-Options','Referrer-Policy'):
            if upstream.headers.get(key): result['headers'][key]=upstream.headers[key]
        if upstream.headers.get('Set-Cookie'): result['cookies']=[upstream.headers['Set-Cookie']]
    finally:
        connection.close()
    server.monitor.scan()
    if path in {'/', '/login'} and result['statusCode'] == 200:
        result['body'] = inline_assets(result['body'])
    if path == '/' and result['statusCode'] == 200:
        result['body'] = result['body'].replace('<body>', '<body><p style="margin:0;padding:10px;background:#fff3cf;text-align:center">Judge sandbox · synthetic data only · temporary data may reset between sessions.</p>')
    result['headers']['Strict-Transport-Security'] = 'max-age=86400'
    result['headers']['X-Content-Type-Options'] = 'nosniff'
    return result
