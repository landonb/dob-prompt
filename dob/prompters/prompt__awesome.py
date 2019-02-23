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

from .prompt_actegory import PromptForActegory
from .prompt_tagcloud import PromptForMoreTags
from .prompter_common import PrompterCommon

__all__ = (
    'AwesomePrompt',
)


class AwesomePrompt(PrompterCommon):
    """
    """

    def __init__(self, controller):
        super(AwesomePrompt, self).__init__()
        self.prompt_actegory = PromptForActegory(controller)
        self.prompt_for_tags = PromptForMoreTags(controller)

    def ask_act_cat(self, filter_activity, filter_category):
        return self.prompt_actegory.ask_act_cat(filter_activity, filter_category)

    def ask_for_tags(self, already_selected, activity):
        return self.prompt_for_tags.ask_for_tags(already_selected, activity)

