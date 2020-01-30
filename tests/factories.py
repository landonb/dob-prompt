# This file exists within 'dob-prompt':
#
#   https://github.com/hotoffthehamster/dob-prompt
#
# Copyright © 2019-2020 Landon Bouma. All rights reserved.
#
# This program is free software:  you can redistribute it  and/or  modify it under the
# terms of the GNU General Public License as published by the Free Software Foundation,
# either version 3  of the License,  or  (at your option)  any later version  (GPLv3+).
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY;  without even the implied warranty of MERCHANTABILITY or  FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU  General  Public  License  for  more  details.
#
# If you lost the GNU General Public License that ships with this software
# repository (read the 'LICENSE' file), see <http://www.gnu.org/licenses/>.

"""Factories to provide easy to use randomized instances of our main objects."""

import datetime

import factory
import faker

from nark.items import Activity, Category, Fact


class CategoryFactory(factory.Factory):
    """Provide a factory for randomized ``nark.Category`` instances."""

    pk = None
    name = factory.Faker('word')

    class Meta:
        model = Category


class ActivityFactory(factory.Factory):
    """Provide a factory for randomized ``nark.Activity`` instances."""

    pk = None
    name = factory.Faker('word')
    category = factory.SubFactory(CategoryFactory)
    deleted = False

    class Meta:
        model = Activity


class FactFactory(factory.Factory):
    """Provide a factory for randomized ``nark.Fact`` instances."""

    pk = None
    activity = factory.SubFactory(ActivityFactory)
    start = faker.Faker().date_time()
    end = start + datetime.timedelta(hours=3)
    description = factory.Faker('paragraph')

    class Meta:
        model = Fact

