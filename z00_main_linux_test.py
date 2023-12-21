# main.py

# from z94_chatgpt_test import app as app2
from threading import Thread

from flask import Flask

from z10_web_server import app as app1

app = Flask(__name__)


def run_gunicorn(app, host="0.0.0.0", port=5000, workers=4):
    options = {
        "bind": f"{host}:{port}",
        "workers": workers,
    }
    from gunicorn.app.base import Application

    class FlaskApplication(Application):
        def init(self, parser, opts, args):
            return {
                "bind": opts.bind,
                "workers": opts.workers,
            }

        def load(self):
            return app

    FlaskApplication().run()


if __name__ == "__main__":
    thread1 = Thread(target=run_gunicorn, args=(app1,))
    # thread2 = Thread(target=run_gunicorn, args=(app2,))

    thread1.start()
    # thread2.start()
