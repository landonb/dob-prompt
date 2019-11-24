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

from gettext import gettext as _

from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.layout.processors import AfterInput, BeforeInput, Transformation
from prompt_toolkit.validation import Validator, ValidationError

from .colors_terrific import TerrificColors1
from .hacky_processor import HackyProcessor
from .interface_bonds import KeyBond
from .parts_suggester import FactPartCompleterSuggester
from .sophisti_prompt import SophisticatedPrompt
from .the_bottom_area import BottomBarArea

__all__ = (
    'PromptForActegory',
    # Private:
    #   'ActegoryCompleterSuggester',
    #   'ActegoryHackyProcessor',
    #   'ActegoryBottomBarArea',
)


class PromptForActegory(SophisticatedPrompt):
    """
    """

    def __init__(self, controller):
        super(PromptForActegory, self).__init__(controller)
        self.activities_cache = {}
        self.categories_cache = {}

        self.activity = ''
        self.category = None
        self.lock_act = False

        # FIXME/2019-11-23 23:18: (lb): Will remove shortly, I affirm!
        self.debug = self.controller.client_logger.debug

    # ***

    @property
    def sep(self):
        return '@'

    def boil_dry_on_backspace_if_text_empty(self, event):
        boiling_dry = not event.current_buffer.text
        self.debug('boiling_dry: {}'.format(boiling_dry))
        if boiling_dry:
            # PPT does not trigger validator unless text changes,
            # and text *is* empty -- before event consumed by PPT
            # -- so we're not expecting a callback. So do things now.
            if self.lock_act:
                self.reset_lock_act(event)
        return boiling_dry

    def handle_backspace_delete_char(self, event):
        return self.boil_dry_on_backspace_if_text_empty(event)

    def handle_backspace_delete_more(self, event):
        if self.boil_dry_on_backspace_if_text_empty(event):
            return True

        # Our wire_hook_backspace callback does not call the PPT basic binding
        # for Ctrl-Backspace/Ctrl-h (which is 'backward-delete-char', the
        # same as for normal Backspace). Instead delete either the category,
        # or the activity. I.e., Ctrl-Backspace is a quick way to delete just
        # the category, but leave the activity.
        if self.lock_act:
            self.reset_lock_act(event)
            return True

        self.activity = ''
        self.reset_lock_act(event)
        return True

    def handle_clear_screen(self, event):
        self.activity = ''
        self.reset_lock_act(event, '')
        return True

    def handle_word_rubout(self, event):
        return self.boil_dry_on_backspace_if_text_empty(event)

    def handle_ctrl_s(self, event):
        # FIXME/2019-11-23 21:12: Respond like ENTER.
        pass

    def handle_escape_hatch(self, event):
        self.update_state(self.activity0, self.category0)
        reset_text = self.lock_act and self.category or self.activity
        event.current_buffer.text = reset_text
        event.current_buffer.cursor_position = len(event.current_buffer.text)
        self.update_input_hint(event, self.lock_act, True)
        return True

    # ***

    def reset_lock_act(self, event, new_text=None):
        self.category = None
        was_lock_act = self.lock_act
        self.lock_act = False
        self.update_input_hint(event, was_lock_act)
        if new_text is None:
            new_text = self.activity
        # (lb): I tested insert_text and it seems to work the same,
        # or at least it seems to update the text, e.g.,
        #   event.current_buffer.insert_text(new_text, overwrite=True)
        # but I'm not sure about the cursor_position, so being deliberate
        # and setting text, then cursor_position explicitly. (And a lot of
        # this is trial and error -- we're messing with both PPT and directly
        # with the renderer.output, which is all hacky, or at least fragile.)
        event.current_buffer.text = new_text
        event.current_buffer.cursor_position = len(event.current_buffer.text)
        if was_lock_act != self.lock_act:
            self.restart_completer(event)

    # (lb): HACK!
    def update_input_hint(self, event, was_lock_at, hack=False):
        # - Note either event.app.current_buffer or event.current_buffer seem to work.
        # - The rendered cursor position should be same as if we calculated:
        #     restore_column = event.app.current_buffer.cursor_position
        #     restore_column += len(self.session_prompt_prefix)
        #     if was_lock_at:
        #         restore_column += len(self.activity)
        #         restore_column += len(self.sep)
        #     affirm(restore_column == event.app.renderer._cursor_pos.x)
        #   but less fragile/obtuse.
        cursor_x = event.app.renderer._cursor_pos.x

        relative_help_row = 1
        event.app.renderer.output.cursor_up(relative_help_row)
        event.app.renderer.output.cursor_backward(cursor_x)

        relative_prompt_row = relative_help_row

        columns = event.app.renderer.output.get_size().columns
        max_col = columns - 2
        prompt_for_what = self.prompt_for_what(max_col)

        print_formatted_text(FormattedText(prompt_for_what))

        recreate_it = '{}{}{}{}'.format(
            self.session_prompt_prefix,
            self.activity or '',
            self.sep,
            self.category or '',
        )
        print_formatted_text(
            FormattedText([
                ('', recreate_it),
            ]),
            end='',
        )

        # (lb): This is insane. Put cursor where it belongs, at end of
        # recreated text.
        # - I think that event.app.renderer._cursor_pos remains unchanged,
        # but in reality the cursor moved (because print_formatted_text),
        # so here we're moving it back to where PPT expects it to be. Or
        # something.
        event.app.renderer.output.cursor_backward(len(recreate_it) - cursor_x)

    # ***

    @property
    def colors(self):
        return TerrificColors1()

    @property
    def fact_part_friendly(self):
        if not self.lock_act:
            # (lb): Just say 'activity', and not
            # the more-correct 'activity@category'.
            part_name = _('activity')
        else:
            part_name = _('category')
        return part_name

    @property
    def history_topic(self):
        return 'actegory'

    @property
    def type_request(self):
        return _('Enter an Activity{}Category').format(self.sep)

    def init_completer(self):
        return ActegoryCompleterSuggester(self.summoned)

    def init_processor(self):
        return ActegoryHackyProcessor(self)

    def init_bottombar(self):
        return ActegoryBottomBarArea(self)

    def toggle_lock_act(self):
        self.lock_act = not self.lock_act

    def prompt_for_what(self, max_col=0):
        prefix = '  '

        what = self.fact_part_friendly.capitalize()
        if not self.lock_act:
            hint = _('Enter the {} followed by `@` or ENTER').format(what)
        else:
            hint = _('Enter the {} followed by Ctrl-S or ENTER').format(what)

        colfill = max_col - len(hint)
        if max_col > 0 and colfill < 0:
            # (lb): 2019-11-23: Assuming this'll work... coverage prove it?
            # BEWARE/2019-11-23 23:03: This is not ANSI-aware!
            hint = hint[:max_col]

        line_parts = []
        line_parts.append(('', prefix))
        line_parts.append(('italic underline', hint))
        if max_col > 0 and colfill > 0:
            line_parts.append(('', ' ' * colfill))
        return line_parts

    # ***

    def update_state(self, activity, category):
        self.activity = activity
        self.category = category

        self.lock_act = False
        if self.activity and self.category:
            self.lock_act = True

    # ***

    def ask_act_cat(self, filter_activity, filter_category):
        self.activity0 = filter_activity
        self.category0 = filter_category

        self.update_state(filter_activity, filter_category)

        self.prepare_session()

        self.keep_prompting_until_satisfied()

        return self.activity, self.category

    def keep_prompting_until_satisfied(self):
        try:
            prompt_once = True
            while prompt_once or (not self.activity or not self.category):
                prompt_once = False
                self.prompt_for_actegory()
        finally:
            self.clean_up_print_text_header()

    def prompt_for_actegory(self):
        self.debug(_('{}@{}').format(self.activity, self.category))

        default = ''
        if self.lock_act:
            default = self.category

        validator = ActegoryValidator(self)

        # Calls PPT's PromptSession.session to run interaction until user
        # hits enter. (So to enter act@gory, user might enter act@[ENTER]
        # first, and then this method will be called again.)
        text = self.session_prompt(default=default, validator=validator)
        self.debug(_('GOT text: {}').format(text))

        self.process_user_reponse(text)
        # Prepare to run again, if necessary.
        #  And start with completions open.
        self.processor.start_completion = True
        self.reset_completer()

    def process_user_reponse(self, text):
        self.debug(_('text: {}').format(text))
        if self.lock_act:
            self.category = text
            # If we prompt again, show activities.
            # EXPLAIN/2019-11-23: (lb): Why would we prompt again? Because no Activity?
            self.lock_act = False
        elif self.sep in text:
            # FIXME/2019-11-23: Support "quoted names"@"foo bar"?
            #                   For now, split at first separator.
            self.activity, self.category = text.split(self.sep, 1)
            if not self.category:
                # Prepare to prompt again, for category.
                self.lock_act = True
        else:
            # No '@' (self.sep), so assume just the activity.
            self.activity = text
            # If we prompt again, show categories.
            self.lock_act = True

    # ***

    def refresh_completions_fact_part(self):
        if self.lock_act:
            results = self.refresh_completions_categories()
        else:
            results = self.refresh_completions_activities()
        return results

    def refresh_completions_categories(self):
        cache_key = (None, self.active_sort.action, self.sort_order)
        if cache_key in self.categories_cache:
            return self.categories_cache[cache_key]

        results = self.controller.categories.get_all(
            include_usage=True,
            sort_col=self.active_sort.action,
            sort_order=self.sort_order,
        )
        self.categories_cache[cache_key] = results
        return results

    def refresh_completions_activities(self):
        # Called on not self.lock_act.
        category = self.refresh_restrict_category()
        cache_key = (category, self.active_sort.action, self.sort_order)
        if cache_key in self.activities_cache:
            return self.activities_cache[cache_key]

        results = self.controller.activities.get_all(
            include_usage=True,
            category=category,
            sort_col=self.active_sort.action,
            sort_order=self.sort_order,
        )
        self.activities_cache[cache_key] = results
        return results

    def refresh_restrict_category(self):
        # Called on not self.lock_act.
        category = False
        if self.category:
            try:
                category = self.controller.categories.get_by_name(self.category)
            except KeyError:
                category = self.category
        return category

    def hydrate_completer(self, results):
        self.completer.hydrate(
            results, skip_category_name=bool(self.category),
        )

    def history_entry_name(self, entry, names):
        entry_name = entry
        if self.lock_act and self.sep in entry:
            # FIXME/2019-11-23: Support "quoted names"@"foo bar"?
            #                   For now, split at first separator.
            _activity_name, category_name = entry.split(self.sep, 1)
            if category_name in names:
                entry_name = None
            else:
                entry_name = category_name
        return entry_name


class ActegoryCompleterSuggester(FactPartCompleterSuggester):
    """
    """

    def hydrate_name(self, item, skip_category_name=False, **kwargs):
        name = item.name
        if not skip_category_name:
            try:
                name = '{}{}{}'.format(item.name, self.sep, item.category.name)
            except AttributeError:
                pass
        return name


class ActegoryHackyProcessor(HackyProcessor):
    """
    """

    def __init__(self, prompter):
        super(ActegoryHackyProcessor, self).__init__(prompter)
        self.before_input = BeforeInput(text=self.prompter.sep)
        self.after_input = AfterInput(text=self.prompter.sep)

    def __repr__(self):
        return 'ActegoryHackyProcessor(%r)' % (self.prompter)

    def apply_transformation(self, transformation_input):
        self.mark_summoned(transformation_input)

        if self.prompter.lock_act:
            # Prefix the input with the Activity, e.g., "act@".
            text = '{}{}'.format(self.prompter.activity, self.prompter.sep)
            self.before_input.text = text
            return self.before_input.apply_transformation(transformation_input)

        elif self.prompter.category:
            # Follow the input with the Category, e.g., "@cat".
            text = '{}{}'.format(self.prompter.sep, self.prompter.category)
            self.after_input.text = text
            return self.after_input.apply_transformation(transformation_input)

        return Transformation(transformation_input.fragments)


class ActegoryBottomBarArea(BottomBarArea):
    """
    """

    def __init__(self, prompter):
        super(ActegoryBottomBarArea, self).__init__(prompter)

    @property
    def say_types(self):
        if not self.prompter.lock_act:
            return _('Activities')
        else:
            return _('Categories')

    def init_hooks_filter(self):
        def brief_scope(binding):
            return self.prompter.fact_part_friendly

        # Option to switch between cats and acts.
        self.filter_bindings = [
            KeyBond(
                'f9',
                brief_scope,
                action=self.toggle_scope,
                briefs=[_('category'), _('activity')],
                highlight=True,
            ),
        ]

    def toggle_scope(self, event):
        self.prompter.toggle_lock_act()
        self.prompter.restart_completer(event)

    def extend_bottom(self, _builder, _dummy_section):
        # The Tag prompt adds a line, so add a blank one now,
        # so prompt height does not grow later.
        return '\n'


class ActegoryValidator(Validator):
    """"""

    def __init__(self, prompt, *args, **kwargs):
        super(ActegoryValidator, self).__init__(*args, **kwargs)
        self.prompt = prompt

    def validate(self, document):
        text = document.text

        self.prompt.debug('text: {}'.format(text))

        message = _('Type `{}` or press ENTER to finish {} name').format(
            self.prompt.sep, self.prompt.fact_part_friendly.capitalize()
        )

        # Use ValidationError to show message in bottom-left of prompt
        # (just above our the_bottom_area footer).
        raise ValidationError(message=message, cursor_position=0)

