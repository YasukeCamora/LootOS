import os
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'LootOS',
        'message': 'API is running successfully'
    })

@app.route('/')
def home():
    return jsonify({
        'message': 'Welcome to LootOS',
        'status': 'online',
        'version': '1.0.0'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
