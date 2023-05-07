"""Uniform messaging service for Python applications."""
from importlib.metadata import PackageNotFoundError, version

try:
    from ._version import version as __version__
except ImportError:  # pragma: nocover
    try:
        __version__ = version("owlery")
    except PackageNotFoundError:
        __version__ = "0.1-dev0"


from .services.email import EmailManager

__all__ = ["EmailManager"]
