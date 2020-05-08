import logging
import os

HERE = os.path.dirname(__file__)

logging.basicConfig(filename=os.path.join(HERE, "logs.txt"), level=logging.DEBUG)


from registry import create_app


application = create_app()
