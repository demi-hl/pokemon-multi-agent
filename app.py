import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from flask import Flask

    class _LazyApp(Flask):
        """Flask subclass that lazy-loads the real app on first request."""
        def __init__(self):
            super().__init__(__name__)
            self._real = None

        def __call__(self, environ, start_response):
            if self._real is None:
                from api.app import create_app
                self._real = create_app()
            return self._real(environ, start_response)

    app = _LazyApp()

except ImportError:
    # Pre-install detection fallback — no packages available yet
    def app(environ, start_response):
        start_response('200 OK', [('Content-type', 'text/plain')])
        return [b'starting']

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    if hasattr(app, 'run'):
        app.run(host='0.0.0.0', port=port)
