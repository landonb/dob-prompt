# -*- coding: utf-8 -*-

# This file is part of 'dob'.
#
# 'dob' is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# 'dob' is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with 'dob'.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, unicode_literals

from .interface_bases import InterfaceStyle

__all__ = [
    'TerrificColors',
]


class TerrificColors(InterfaceStyle):
    """
    """

    # (lb): I used colors from a palette I made, with no particular
    # goal other than being light and anti-distracting to the viewer.
    # They ended up kinda lightish redish brownish pinkish.
    #   http://paletton.com/#uid=1000u0kg0qB6pHIb0vBljljq+fD
    #
    # FIXME: Adjust colors based on terminal palette, i.e., support light backgrounds.
    #        (I've chosen colors that look good to me (I have no colorblindness)
    #        in a terminal configured how I like, which is white text on true black.)
    #

    @property
    def color_1(self):
        return 'AA3939'

    @property
    def color_2(self):
        return 'FCA5A5'

    @property
    def color_3(self):
        return '7D1313'

