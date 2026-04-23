"""Test configuration for XCC integration tests.

Import-path rules used by every test file:

* The repository root is on ``sys.path`` so that ``custom_components.xcc.<module>``
  works as a proper package import.
* The ``custom_components`` directory is on ``sys.path`` so that short-form
  ``import xcc.<module>`` also works.
* The ``custom_components/xcc`` directory is **never** on ``sys.path`` —
  doing so shadows the Python standard library's ``select`` module because
  the integration also ships a ``select.py`` platform file.

Any test that needs to import integration code should rely on these paths
and use either ``from custom_components.xcc.<module> import X`` or
``from xcc.<module> import X``. Do not call ``sys.path.insert`` from
individual test files.
"""

from __future__ import annotations

import os
import sys

# Pre-cache the stdlib ``select`` and ``selectors`` modules in ``sys.modules``
# before any test file gets a chance to prepend ``custom_components/xcc`` to
# ``sys.path``. Once these are cached, Python's import machinery returns the
# cached stdlib version on every subsequent ``import select`` regardless of
# what path manipulation happens later. Without this defence the local
# ``custom_components/xcc/select.py`` hijacks any transitive ``import select``
# (triggered, for example, by ``asyncio``/``socket``/``selectors``) and blows
# up the test session with ``ModuleNotFoundError: No module named 'homeassistant'``.
import select  # noqa: F401  pre-cache stdlib module
import selectors  # noqa: F401  pre-cache stdlib module

import pytest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_CC_DIR = os.path.join(_REPO_ROOT, "custom_components")
_XCC_DIR = os.path.join(_CC_DIR, "xcc")

for _p in (_REPO_ROOT, _CC_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Guard: remove any stray entries pointing at the xcc package directory,
# which would shadow the stdlib ``select`` module.
sys.path[:] = [p for p in sys.path if os.path.normcase(os.path.abspath(p)) != os.path.normcase(_XCC_DIR)]


@pytest.fixture
def sample_data_dir():
    """Return the path to the sample data directory."""
    return os.path.join(os.path.dirname(__file__), "sample_data")


@pytest.fixture
def repo_root():
    """Return the repository root directory."""
    return _REPO_ROOT
