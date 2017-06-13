from flask import Flask
import os
import threading
from threading import Thread
from app import app
from app import tfcalc
port = int(os.getenv("PORT", 3000))

def running():
    app.run(host='0.0.0.0', port=port)

def calc():
    tfcalc.test()


if __name__ == '__main__':
    Thread(target=running).start()
    Thread(target= calc).start()