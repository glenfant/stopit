# -*- coding: utf-8 -*-
"""
======
stopit
======

Public resources from ``stopit``
"""

from .utils import LOG, TimeoutException
from .threadstop import ThreadingTimeout, async_raise, threading_timeoutable
from .signalstop import SignalTimeout, signal_timeoutable

# PEP 396 style version marker
try:
    from importlib.metadata import version  # Python >=3.8
    __version__ = version(__name__)
except:
    try:
        import pkg_resources  # Deprecated in recent setuptools
        __version__ = pkg_resources.get_distribution(__name__).version
    except:
        LOG.warning("Could not get the package version from importlib or pkg_resources")
        __version__ = 'unknown'

__all__ = (
    'ThreadingTimeout', 'async_raise', 'threading_timeoutable',
    'SignalTimeout', 'signal_timeoutable'
)
