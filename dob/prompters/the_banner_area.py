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

from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText

from .interface_crown import BannerBarBuilder

__all__ = (
    'BannerBarArea',
)


class BannerBarArea(object):
    """
    """

    def __init__(self, prompter):
        self.prompter = prompter
        self.help_page_number = 0
        self.assemble_hints()

    def stand_up(self, key_bindings):
        self.wire_hooks(key_bindings)
        self.build_builder()

    def wire_hooks(self, key_bindings):
        self.wire_hook_help(key_bindings)

    def wire_hook_help(self, key_bindings):
        keycode = ('escape', 'h')

        def handler(event):
            self.cycle_help(event)
        key_bindings.add(*keycode)(handler)

    def build_builder(self, term_width=0):
        stretch_width = self.prompter.bottombar.builder.first_line_len
        self.builder = BannerBarBuilder(
            colors=self.prompter.colors,
            term_width=term_width,
        )
        self.content = (
            self.prompter.bannerbar_title,
            self.prompter.type_request,
            self.help_section_text,
        )
        self.help_section_idx = 2
        self.builder.add_content(*self.content, width=stretch_width)

    @property
    def completion_hints(self):
        return [
            'Press <Alt-h> for help.',
        ]

    def assemble_hints(self):
        self.help_pages = (
            self.completion_hints
            + self.prompter.completion_hints
            + ['']  # Cycle through to blank line.
        )

    def help_section_text(self):
        help_text = self.help_pages[self.help_page_number].format(
            part_type=self.prompter.fact_part_friendly,
        )
        return help_text

    def cycle_help(self, event):
        self.help_page_number = (self.help_page_number + 1) % len(self.help_pages)

        # (lb): This is a hack to overwrite the banner, which is not part
        # of the PPT app -- we wrote the banner first, before starting the
        # prompt. (I could learn PPT layouts and rewrite our code to manage
        # the banner from within the PPT app context... but I won't; not now.)
        restore_column = event.app.current_buffer.cursor_position
        # The cursor position is relative to the PPT buffer which starts
        # after the prefix we told the prompt to draw.
        restore_column += len(self.prompter.session_prompt_prefix)
        # The hack gets hackier: Add one for the '@' if BeforeInput set.
        restore_column += 1 if self.prompter.restrict_category else 0
        # The help row is this many rows above the prompt: As many rows as
        # the banner, minus the row that the help is on, plus one row for
        # the blank line between the banner and the prompt.
        relative_help_row = 1 + (len(self.content) - self.help_section_idx)
        # "Up, up, up, up, up, up raises
        #  The stakes of the game."
        event.app.renderer.output.cursor_up(relative_help_row)
        event.app.renderer.output.cursor_backward(restore_column)
        # Hack-within-a-hack. Ask our banner builder to build us just the
        # row in question, and tell PPT to dump it where the cursor's at.
        print_formatted_text(FormattedText(
            self.builder.render_one(self.help_section_idx)
        ))
        # Finally, restore the cursor. The print added a newline, so
        # the row is down one less than we moved up.
        relative_prompt_row = relative_help_row - 1
        event.app.renderer.output.cursor_down(relative_prompt_row)
        event.app.renderer.output.cursor_forward(restore_column)

