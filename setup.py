#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of 'dob-prompt'.
#
# 'dob-prompt' is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# 'dob-prompt' is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with 'dob-prompt'.  If not, see <http://www.gnu.org/licenses/>.

"""
Packaging instruction for setup tools.

Refs:

  https://setuptools.readthedocs.io/

  https://packaging.python.org/en/latest/distributing.html

  https://github.com/pypa/sampleproject
"""

from setuptools import find_packages, setup

# *** Package requirements.

requirements = [
    # https://github.com/pytest-dev/apipkg
    'apipkg',
# FIXME/2020-01-05 17:57: Require dob, or the other way around?
    # The dob CLI core.
    'dob',
# FIXME/2020-01-05 17:31: Scrub the `future` library, but now it is!
    # Compatibility layer between Python 2 and Python 3.
    #  https://python-future.org/
    'future',
    # Vocabulary word pluralizer.
    #  https://github.com/ixmatus/inflector
    'Inflector',
    # Elapsed timedelta formatter, e.g., "1.25 days".
    'human-friendly_pedantic-timedelta >= 0.0.6',  #  Imports as pedantic_timedelta.
    # Amazeballs prompt library.
    # FIXME/2019-02-21: Submit PR. Until then, whose fork?
    'prompt-toolkit-dob >= 2.0.9',  # Imports as prompt_toolkit.
# FIXME/2020-01-05 17:50: Remove 'six', 'future', etc.
    # Virtuous Six Python 2 and 3 compatibility library.
    #  https://six.readthedocs.io/
    'six',
]

# *** Minimal setup() function -- Prefer using config where possible.

# (lb): All settings are in setup.cfg, except identifying packages.
# (We could find-packages from within setup.cfg, but it's convoluted.)

setup(
    install_requires=requirements,
    packages=find_packages(exclude=['tests*']),
    # Tell setuptools to determine the version
    # from the latest SCM (git) version tags.
    #
    # Without the following two lines, e.g.,
    #   $ python setup.py --version
    #   3.0.0a31
    # But with 'em, e.g.,
    #   $ python setup.py --version
    #   3.0.0a32.dev3+g6f93d8c.d20190221
    # Or, if the latest commit is tagged,
    # and your working directory is clean,
    # then the version reported (and, e.g.,
    # used on make-dist) will be from tag.
    # Ref:
    #   https://github.com/pypa/setuptools_scm
    setup_requires=['setuptools_scm'],
    use_scm_version=True,
)

