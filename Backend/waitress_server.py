from waitress import serve
import flask_app as app_file



serve(app_file.app, host='0.0.0.0', port=80)

