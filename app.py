import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from api.app import create_app
    app = create_app()
except Exception:
    # Fallback minimal app for Render detection phase (before pip install)
    from flask import Flask, jsonify
    app = Flask(__name__)

    @app.route('/health')
    def health():
        return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5001)))
