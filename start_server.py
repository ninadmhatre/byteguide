from byteguide import app
from byteguide.config import config

if __name__ == "__main__":
    app.run(host=config.host, port=config.port, debug=config.debug)
