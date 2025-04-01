# SPDX-FileCopyrightText: 2025 Max Mehl <https://mehl.mx>
#
# SPDX-License-Identifier: GPL-3.0-only

"""WSGI entry point for the Home Stream application."""

from .app import create_app as build_app


def create_app(config_path):
    """Create a Flask application instance."""
    return build_app(config_path)
