# SPDX-FileCopyrightText: 2025 Max Mehl <https://mehl.mx>
#
# SPDX-License-Identifier: GPL-3.0-only

"""Home Stream Web Application"""

import argparse
import os

from flask import (
    Flask,
    abort,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

from home_stream.helpers import (
    file_type,
    get_stream_token,
    load_config,
    secure_path,
    serve_via_gunicorn,
    validate_user,
)


def create_app(config_path: str) -> Flask:
    """Create a Flask application instance."""
    app = Flask(__name__)
    load_config(app, config_path)
    init_routes(app)
    return app


def init_routes(app: Flask):
    """Initialize routes for the Flask application."""

    @app.context_processor
    def inject_auth():
        return {
            "auth_password": getattr(request, "password", ""),
            "stream_token": get_stream_token(session["username"]) if "username" in session else "",
        }

    def is_authenticated():
        return session.get("username") in app.config["USERS"]

    @app.route("/login", methods=["GET", "POST"])
    def login():
        error = None
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            if validate_user(username, password):
                session["username"] = username
                return redirect(request.args.get("next") or url_for("index"))
            error = "Invalid credentials"
        return render_template("login.html", error=error)

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.route("/")
    def index():
        if not is_authenticated():
            return redirect(url_for("login", next=request.full_path))
        return redirect(url_for("browse", subpath=""))

    @app.route("/browse/", defaults={"subpath": ""})
    @app.route("/browse/<path:subpath>")
    def browse(subpath):
        if not is_authenticated():
            return redirect(url_for("login", next=request.full_path))

        current_path = secure_path(subpath)
        if not os.path.isdir(current_path):
            abort(404)

        folders, files = [], []
        for entry in os.listdir(current_path):
            full = os.path.join(current_path, entry)
            rel = os.path.join(subpath, entry)
            if os.path.isdir(full) and not entry.startswith("."):
                folders.append((entry, rel))
            elif os.path.isfile(full):
                ext = os.path.splitext(entry)[1].lower().strip(".")
                if ext in app.config["MEDIA_EXTENSIONS"]:
                    files.append((entry, rel))

        folders.sort(key=lambda x: x[0].lower())
        files.sort(key=lambda x: x[0].lower())

        return render_template(
            "browse.html",
            path=subpath,
            folders=folders,
            files=files,
            username=session.get("username"),
        )

    @app.route("/play/<path:filepath>")
    def play(filepath):
        if not is_authenticated():
            return redirect(url_for("login", next=request.full_path))

        secure_path(filepath)
        return render_template(
            "play.html",
            path=filepath,
            mediatype=file_type(filepath),
            username=session.get("username"),
        )

    @app.route("/dl/<path:filepath>")
    def download(filepath):
        if not is_authenticated():
            return redirect(url_for("login", next=request.full_path))

        full_path = secure_path(filepath)
        if os.path.isfile(full_path):
            return send_file(full_path)
        abort(404)

    @app.route("/dl-token/<username>/<token>/<path:filepath>")
    def download_token_auth(username, token, filepath):
        expected = get_stream_token(username)
        if token != expected:
            abort(403)
        full_path = secure_path(filepath)
        if os.path.isfile(full_path):
            return send_file(full_path)
        abort(404)


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-c", "--config-file", required=True, help="Path to the app's config file (YAML format)"
    )
    parser.add_argument("--host", default="localhost", help="Hostname of the server")
    parser.add_argument("-p", "--port", type=int, default=8000, help="Port of the server")
    parser.add_argument(
        "-vv",
        "--debug",
        action="store_true",
        help="Enable debug mode. Starts a Flask debug server instead of Gunicorn.",
        default=False,
    )

    args = parser.parse_args()

    if args.debug:
        app = create_app(config_path=os.path.abspath(args.config_file))
        app.run(debug=args.debug, host=args.host, port=args.port)
    else:
        serve_via_gunicorn(config_file=args.config_file)


if __name__ == "__main__":
    main()
