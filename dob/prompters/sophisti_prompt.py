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

from collections import namedtuple

from gettext import gettext as _

from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.auto_suggest import AutoSuggest
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import FileHistory, InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import CompleteStyle

from .. import __package_name__
from ..cmd_config import AppDirs, get_appdirs_subdir_file_path
from ..helpers.path import touch
from .prompter_common import PrompterCommon
from .the_banner_area import BannerBarArea

__all__ = (
    'SophisticatedPrompt',
    # Private:
    #  'HamsterPartAutoSuggest',
)


class HamsterPartAutoSuggest(AutoSuggest):
    """
    """

    def __init__(self, completer):
        self.completer = completer

    def get_suggestion(self, buffer, document):
        return self.completer.get_suggestion(buffer, document)


class SophisticatedPrompt(PrompterCommon):
    """
    """

    def __init__(self, controller):
        self.controller = controller
        self.history = self.init_history()
        self.completer = self.init_completer()
        self.processor = self.init_processor()
        self.bannerbar = self.init_bannerbar()
        self.bottombar = self.init_bottombar()
        self.key_bindings = None
        self.session = None
        self.sort_order = None
        self.restrict_category = False
        self.showing_completions = False

    # ***

    @property
    def bannerbar_title(self):
        return __package_name__

    @property
    def colors(self):
        raise NotImplementedError

    @property
    def fact_part_friendly(self):
        raise NotImplementedError

    @property
    def history_topic(self):
        raise NotImplementedError

    @property
    def type_request(self):
        raise NotImplementedError

    # ***

    def init_history(self):
        file_path = self.history_path
        if file_path:
            # Make sure it exists, else "No such file or directory".
            touch(file_path)
            history = FileHistory(file_path)
        else:
            history = InMemoryHistory()
        return history

    def init_completer(self):
        raise NotImplementedError

    def init_processor(self):
        raise NotImplementedError

    def init_bannerbar(self):
        return BannerBarArea(self)

    def init_bottombar(self):
        raise NotImplementedError

    # ***

    @property
    def complete_while_typing(self):
        return self.bottombar.complete_while_typing

    @property
    def enable_history_search(self):
        return self.bottombar.enable_history_search

    @property
    def active_sort(self):
        return self.bottombar.active_sort

    @active_sort.setter
    def active_sort(self, value):
        self.bottombar.active_sort = value

    @property
    def default_sort(self):
        return self.bottombar.default_sort

    @property
    def sorting_by_history(self):
        return self.bottombar.sorting_by_history

    # ***

    def prepare_session(self):
        # Get the terminal size measure function.
        self.get_size = self.prompt_session.app.renderer.output.get_size

        self.stand_up_banner_and_bottom()

        # If caller is interrogating for more than one Fact, remember
        # the settings from the previous run (use self.active_sort).
        binding = self.active_sort or self.default_sort

        self.session = None
        self.showing_completions = False

        self.reset_completer(binding)

        self.session = self.prompt_session

        self.print_text_header()

    # ***

    @property
    def bottom_toolbar(self):
        return self.bottombar.builder.parts

    def bottom_toolbar_reset(self):
        self.bottombar.builder.clear()
        self.session.bottom_toolbar = self.bottom_toolbar

    # ***

    def stand_up_banner_and_bottom(self):
        self.key_bindings = KeyBindings()
        self.bottombar.stand_up(self.key_bindings)
        self.bannerbar.stand_up(self.key_bindings)

    # ***

    def reset_completer(self, binding=None, toggle_ok=False):
        self.bannerbar.builder.clear()
        self.bottombar.builder.clear()

        self.ensure_active(binding, toggle_ok)

        # Refresh the bottom toolbar.
        if self.session is not None:
            self.session.bottom_toolbar = self.bottom_toolbar

        # Refresh, well, duh, the completions.
        # (lb): We do this now, on startup, rather than lazy-loading later,
        # because we want to make suggestions as the user types. So we need
        # results now.
        self.refresh_completions()

    def ensure_active(self, binding=None, toggle_ok=False):
        if self.active_sort is None:
            self.sort_order = 'desc'

        if binding is not None:
            if self.active_sort == binding:
                if toggle_ok:
                    if self.sort_order != binding.sort_order:
                        # Toggle: sort_order, !sort_order, hide-completions
                        # FIXME: (lb): I'm not sold on this behavior. Make cfgable?
                        self.showing_completions = False
                    self.sort_order = 'asc' if self.sort_order == 'desc' else 'desc'
            else:
                self.active_sort = binding
                self.sort_order = binding.sort_order

    # ***

    FakeUsageResult = namedtuple('FakeUsageResult', ('name', 'usage', 'span'))

    FakeUsageWrapper = namedtuple('FakeUsageWrapper', ('item', 'uses', 'span'))

    def refresh_completions(self):
        results = self.fetch_results()
        self.hydrate_completer(results)

    def fetch_results(self):
        if self.sorting_by_history:
            results = self.refresh_completions_history()
        else:
            results = self.refresh_completions_fact_part()
        return results

    def hydrate_completer(self, results):
        self.completer.hydrate(results)

    def refresh_completions_history(self):
        results = []
        names = set()
        # FIXME: (lb): Does this make any sense?
        for entry in list(self.history.load_history_strings()):
            entry_name = self.history_entry_name(entry, names)
            if entry_name is None or entry_name in names:
                continue
            names.add(entry_name)
            result = SophisticatedPrompt.FakeUsageResult(entry_name, None, None)
            results.append(SophisticatedPrompt.FakeUsageWrapper(result, None, None))
        if self.sort_order == 'asc':
            results.reverse()
        return results

    def history_entry_name(self, entry, _names):
        return entry

    # ***

    def print_text_header(self):
        term_width = self.get_size()[1]
        self.bannerbar.build_builder(term_width)
        parts = self.bannerbar.builder.parts
        # (lb): Note that we just print the banner to the terminal and
        # forget about it, i.e., this text is not managed by the PPT.
        # (We do, however, edit the help text line if the user cycles
        # through the help pages, but we just hack the cursor with
        # carnal knowledge of the screen, rather than calling the builder
        # to regenerate its parts.) So the builder gets used once, here,
        # on startup, and later we just redraw the help line as needed.
        print_formatted_text(FormattedText(parts))

    @property
    def completion_hints(self):
        return [
            _('Press TAB to show a list of {part_type} suggestions.'),
            _('Use ARROW keys to navigate list of suggestions,'
              ' and ENTER to choose one.'),
            _('As you type, the best match is shown. Use RIGHT → ARROW to accept it.'),
            _('Press UP ↑ ARROW to cycle through previous values you have entered.'),
            _('Use F-keys to change how the list of suggestions is sorted.'),
            _('You can also use your favorite Readline keys.'
              ' E.g., Ctrl-u deletes to start of line.'),
        ]

    @property
    def completion_hints_count(self):
        return len(self._completion_hints)

    def completion_hints_page(self, page):
        return self.completion_hints[page]

    # ***

    def clean_up_print_text_header(self):
        """
        Clear the banner manually, which was dumped to the terminal
        before the prompt ran, so erase_when_done did not clean it.
        """
        up_count = len(self.bannerbar.builder.sections) + 1
        self.session.app.renderer.output.cursor_up(up_count)
        # (lb): Without flush(), erase_down() erases from old position.
        self.session.app.renderer.output.flush()
        self.session.app.renderer.output.erase_down()
        self.session.app.renderer.output.flush()

    # ***

    @property
    def prompt_session(self):
        session = PromptSession(
            erase_when_done=True,
            history=self.history,
            enable_history_search=self.enable_history_search,
            auto_suggest=HamsterPartAutoSuggest(self.completer),
        )
        return session

    @property
    def session_prompt_prefix(self):
        return '> '

    # Called in a loop by the actegory- or tagcloud-asker, either until
    # valid actegory entered, or until user is finished entering tags.
    def session_prompt(self, default=''):
        text = self.session.prompt(
            self.session_prompt_prefix,
            default=default,

            bottom_toolbar=self.bottom_toolbar,
            # FIXME: (lb): Add animation? Then redraw periodically; else, no cares.
            #  # Call self.bottom_toolbar periodically.
            #  refresh_interval=0.5,

            completer=self.completer,
            complete_in_thread=True,
            complete_style=CompleteStyle.MULTI_COLUMN,
            complete_while_typing=self.complete_while_typing,

            input_processors=[self.processor, ],

            key_bindings=self.key_bindings,

            style=self.bottombar.prompt_style,
        )

        return text

    # ***

    def summoned(self, showing_completions):
        self.showing_completions = showing_completions
        self.session.bottom_toolbar = self.bottom_toolbar

    # ***

    def restart_completer(self, event, binding=None, toggle_ok=False):
        # (lb): Docs indicate set_completions is part of buffer, but not so:
        #   NOPE: event.app.current_buffer.set_completions(completions=...)
        # Docs also say start_completion part of CLI object, but it's in buffer?
        #  In any case, cancel the current completion, and start a new one.
        self.showing_completions = True
        if event.app.current_buffer.complete_state:
            event.app.current_buffer.cancel_completion()
        else:
            # Only happens first time user presses F-key,
            #  if they haven't already pressed <TAB>.
            toggle_ok = False
        self.reset_completer(binding=binding, toggle_ok=toggle_ok)
        if self.showing_completions:
            event.app.current_buffer.start_completion()

    # ***

    DEFAULT_HIST_PATH_DIR = 'history'

    @property
    def history_path(self):
        """
        Return the path to the history file for a specific topic.

        Args:
            topic (text_type): Topic name, to distinguish different histories.

        Returns:
            str: Fully qualified path to history file for specified topic.
        """
        hist_path = get_appdirs_subdir_file_path(
            file_basename=self.history_topic,
            dir_dirname=SophisticatedPrompt.DEFAULT_HIST_PATH_DIR,
            appdirs_dir=AppDirs.user_cache_dir,
        )
        return hist_path

