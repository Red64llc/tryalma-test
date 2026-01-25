"""Flask web application for document upload UI.

This module provides a Flask-based web interface for uploading passport
and G-28 documents, extracting data using existing services, and populating
forms with the extracted information.
"""

from tryalma.webapp.app import create_app

__all__ = ["create_app"]
