from z10_web_server import app as app1
from z94_chatgpt_test import app as app2
from threading import Thread
from flask import Flask

app = Flask(__name__)
app2 = Flask(__name__)


def run_flask_app(app):
    app.run()


if __name__ == "__main__":
    # thread1 = Thread(target=run_flask_app, args=(app1,))
    thread2 = Thread(target=run_flask_app, args=(app2,))

    # thread1.start()
    thread2.start()
