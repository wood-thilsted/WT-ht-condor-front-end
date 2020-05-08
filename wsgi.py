import logging
import os
import sys

HERE = os.path.dirname(__file__)
sys.path.append(HERE)

logging.basicConfig(filename=os.path.join(HERE, "logs.txt"), level=logging.DEBUG)

from registry import create_app

application = create_app()
