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

from prompt_toolkit.layout.processors import Processor, Transformation

__all__ = (
    'HackyProcessor',
)


class HackyProcessor(Processor):
    """
    A `Processor` that kludges updating the bottom bar according to whether
    the completion list is showing. (lb): Because I couldn't figure out how
    else to hook the showing/hiding of the completion list.
    """

    def __init__(self, prompter):
        super(HackyProcessor, self).__init__()
        self.prompter = prompter
        self.start_completion = False

    def __repr__(self):
        return (
            '<{}.HackyProcessor at 0x{}'.format(
                self.__name__, hex(id(self)),
            )
        )

    def apply_transformation(self, transformation_input):
        self.mark_summoned(transformation_input)
        return Transformation(transformation_input.fragments)

    def mark_summoned(self, transformation_input):
        # (lb): This is such a hack! This is called on prompt startup,
        # and it's the only hook I've figured to use so far to do things
        # that I cannot otherwise do through the session construction, or
        # the prompt method. Here, if the prompt was called again
        # automatically, show the autocomplete list automatically, so
        # the user is not confused by the prompt reappeared.
        complete_state = self.prompter.session.app.current_buffer.complete_state

        if not complete_state and self.start_completion:
            self.start_completion = False
            transformation_input.buffer_control.buffer.start_completion()

        # (lb): This is also a hack! See if the app is showing the completions
        # list and redraw the bottom bar accordingly. (I first tried checking
        # transformation_input.fragments[0][1] == '' but when you cycle through
        # the completion list, there's an empty string between the start and
        # the end of the list you can access. So dig deep into the app for the
        # answer.)
        showing_completions = complete_state is not None
        self.prompter.summoned(showing_completions=showing_completions)

