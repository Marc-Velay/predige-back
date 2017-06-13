from flask import Flask
import os
from app import app
port = int(os.getenv("PORT", 3000))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)