from flask import Flask

from byteguide.config import config
from byteguide.routes.common import common_routes
from byteguide.routes.display import display_routes
from byteguide.routes.manage import manage_routes
from byteguide.libs.jinja_fltrs import register_filters

app = Flask(__name__)

app.config.from_object(config)
app.config["MAX_CONTENT_LENGTH"] = config.max_content_mb * 1024 * 1024

app.register_blueprint(common_routes)
app.register_blueprint(display_routes)
app.register_blueprint(manage_routes)

register_filters()
