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
        self.category = ''
        self.lock_act = False

        # FIXME/2019-11-23 23:18: (lb): Will remove shortly, I affirm!
        self.debug = self.controller.client_logger.debug

    # ***

    @property
    def sep(self):
        return '@'

    # ***

    # BOIL-DRY handlers: When user deletes backwards, double-deleting the
    # empty string can switch the prompt from Category input back to
    # Activity input (which affects what the prompt looks like, what
    # suggestions it gives, what the hint above the prompt reads, what
    # the bottom bar displays, etc.).

    def boil_dry_on_backspace_if_text_empty(self, event):
        boiling_dry = not event.current_buffer.text
        self.debug('boiling_dry: {}'.format(boiling_dry))
        if boiling_dry:
            # PPT does not trigger validator unless text changes,
            # and text *is* empty -- before event consumed by PPT
            # -- so we're not expecting a callback. So do things now.
            if self.lock_act:
                self.forget_category(event)
        return boiling_dry

    def handle_backspace_delete_char(self, event):
        boiling_dry = self.boil_dry_on_backspace_if_text_empty(event)
        if not boiling_dry and event.current_buffer.cursor_position == 0:
            # Cursor is all the way left... do it do it do it
            self.toggle_lock_act(event)
            return True
        return boiling_dry

    def handle_backspace_delete_more(self, event):
        if self.boil_dry_on_backspace_if_text_empty(event):
            return True

        # Our wire_hook_backspace callback does not call the PPT basic binding
        # for Ctrl-Backspace/Ctrl-h (which is 'backward-delete-char', the
        # same as for normal Backspace). Instead delete either the category,
        # or the activity. I.e., Ctrl-Backspace is a quick way to delete just
        # the category, but leave the activity.
        if self.lock_act:
            self.forget_category(event)
            return True

        self.activity = ''
        self.forget_category(event)
        return True

    def handle_clear_screen(self, event):
        self.activity = ''
        self.forget_category(event, '')
        return True

    def handle_word_rubout(self, event):
        return self.boil_dry_on_backspace_if_text_empty(event)

    def handle_accept_line(self, event):
        if not self.lock_act:
            activity = event.current_buffer.text
            self.lock_activity(activity, lock_act=True)
            # (lb): While we don't show the completions drop down when the
            # prompt is first started (i.e., when prompting for Activity
            # name), I think it's nice to show the drop down automatically
            # for the latter Category half of the prompt session. There are
            # generally fewer Categories than Activities, and once the user
            # puts in a few, they're unlikely to add more, so it makes sense
            # to just show the list without waiting for user to trigger it.
            # Also, the user is more familiar with the prompt now, which is
            # one reason we don't want to show the completions drop down
            # immediately on prompt, because it can make the interface look
            # daunting.
            self.session.layout.current_buffer.start_completion()
            return True
        # Let PPT process the call, which will spit out in
        # prompt_for_actegory, but we can set the category
        # here, so it's near lock_activity which set activity.
        self.category = event.current_buffer.text
        return False

    def handle_menu_complete(self, event):
        # PPT's tab complete using the first completion, not the suggestion.
        # Here we fix that.

        # FIXME/2019-11-24: (lb): Do we need this for tags, too?
        # - We could just move to base class if so.

        suggestion = event.current_buffer.suggestion
        if suggestion and suggestion.text:
            # Pretty much exactly what load_auto_suggest_bindings does.
            cb = event.current_buffer
            cb.insert_text(suggestion.text)
            return True

        # Else, default to normal TAB behavior, which cycles through
        # list of completions ('menu-complete').
        return False

    def handle_content_reset(self, event):
        self.update_state(self.activity0, self.category0)
        reset_text = self.lock_act and self.category or self.activity
        event.current_buffer.text = reset_text
        event.current_buffer.cursor_position = len(event.current_buffer.text)
        self.update_input_hint(event, self.lock_act, True)
        return True

    def handle_escape_dismiss(self, event):
        self.session.layout.current_buffer.cancel_completion()
        return True

    # ***

    def forget_category(self, event, new_text=None):
        self.category = ''
        self.reset_lock_act(event, new_text)

    def reset_lock_act(self, event, new_text=None):
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

    def update_input_hint(self, event, was_lock_at, hack=False):
        self.update_input_hint_renderer(event.app.renderer, was_lock_at, hack)

    # (lb): HACK!
    def update_input_hint_renderer(self, renderer, was_lock_at, hack=False):
        # - Note either event.app.current_buffer or event.current_buffer seem to work.
        # - The rendered cursor position should be same as if we calculated:
        #     restore_column = event.app.current_buffer.cursor_position
        #     restore_column += len(self.session_prompt_prefix)
        #     if was_lock_at:
        #         restore_column += len(self.activity)
        #         restore_column += len(self.sep)
        #     affirm(restore_column == event.app.renderer._cursor_pos.x)
        #   but less fragile/obtuse.
        cursor_x = renderer._cursor_pos.x

        relative_help_row = 1
        renderer.output.cursor_up(relative_help_row)
        renderer.output.cursor_backward(cursor_x)

        relative_prompt_row = relative_help_row

        columns = renderer.output.get_size().columns
        max_col = columns - 2
        prompt_for_what = self.prompt_for_what(max_col)

        print_formatted_text(FormattedText(prompt_for_what))

        recreate_it = '{}{}{}{}'.format(
            self.session_prompt_prefix,
            self.activity,
            self.sep,
            self.category,
        )
        print_formatted_text(
            FormattedText([
                ('', recreate_it),
            ]),
            end='',
        )

        # (lb): This is insane. Put cursor where it belongs, at end of
        # recreated text.
        # - I think that renderer._cursor_pos remains unchanged,
        # but in reality the cursor moved (because print_formatted_text),
        # so here we're moving it back to where PPT expects it to be. Or
        # something.
        renderer.output.cursor_backward(len(recreate_it) - cursor_x)

    # ***

    @property
    def colors(self):
        return TerrificColors1()

    @property
    def edit_part_type(self):
        if not self.lock_act:
            # (lb): Just say 'activity', and not
            # the more-correct 'activity@category'.
            part_meta = _('activity')
        else:
            part_meta = _('category')
        return part_meta

    @property
    def edit_part_text(self):
        if not self.lock_act:
            part_text = self.activity
        else:
            part_text = self.category
        return part_text

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

    def toggle_lock_act(self, event):
        if not self.lock_act:
            activity = event.current_buffer.text
            self.lock_activity(activity)
        else:
            self.category = event.current_buffer.text
            self.reset_lock_act(event)

    def prompt_for_what(self, max_col=0):
        prefix = '  '

        what = self.edit_part_type.capitalize()
        # (lb): In addition to keys hinted, you can also Ctrl-SPACE. For now.
        if not self.lock_act:
            hint = _('Enter the {} then hit ENTER or `@`').format(what)
        else:
            hint = _('Enter the {} then hit ENTER or Ctrl-s').format(what)

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

    def update_state(self, activity, category, lock_act=False, startup=False):
        self.activity = activity
        self.category = category

        was_lock_act = self.lock_act

        self.lock_act = False
        if self.activity or lock_act:
            self.lock_act = True

        if (
            (not startup)
            and (self.session is not None)
            and (was_lock_act != self.lock_act)
        ):
            self.update_input_hint_renderer(self.session.app.renderer, was_lock_act)
            self.restart_completer(event=None)

    def lock_activity(self, activity, lock_act=False):
        self.session.layout.current_buffer.text = self.category
        self.session.layout.current_buffer.cursor_position = (
            len(self.session.layout.current_buffer.text)
        )
        self.update_state(activity, self.category, lock_act=lock_act)

    # ***

    def ask_act_cat(self, filter_activity, filter_category):
        self.activity0 = filter_activity
        self.category0 = filter_category

        self.update_state(filter_activity, filter_category, startup=True)

        self.prepare_session()

        self.keep_prompting_until_satisfied()

        return self.activity, self.category

    def keep_prompting_until_satisfied(self):
        try:
            self.prompt_for_actegory()
        finally:
            self.clean_up_print_text_header()

    def prompt_for_actegory(self):
        self.debug(_('{}@{}').format(self.activity, self.category))

        default = ''
        if self.lock_act:
            default = self.category

        self.validator = ActegoryValidator(self)
        self.validator.update_last_seen()

        # Calls PPT's PromptSession.session to run interaction until user
        # hits enter. (So to enter act@gory, user might enter act@[ENTER]
        # first, and then this method will be called again.)
        text = self.session_prompt(default=default, validator=self.validator)
        self.debug(_('GOT text: {}').format(text))

        # We set category in handle_accept_line.
        self.controller.affirm(self.category == text)

        # Once created, the caller is free to run the prompt again.
        # (lb): Old behavior was to prompt first for Activity and then to run
        # the prompt again for the Category name. Also, on the second prompt,
        # for the Category, the completions dropdown was shown automatically:
        #   # Start with completions open.
        #   self.processor.start_completion = True
        #   self.reset_completer()
        # But we no longer do that. See comments at:
        #   HackyProcessor.mark_summoned
        # Basically, the Awesome Prompt interface is pretty busy as it is, so it's
        # better to show a clean prompt at first -- and let the user see what the
        # prompt controls are -- before showing the user a huge dropdown of all their
        # data (Activity or Category names).

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
            return self.prompter.edit_part_type

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
        self.prompter.toggle_lock_act(event)

    def extend_bottom(self, _builder, _dummy_section):
        # The Tag prompt adds a line, so add a blank one now,
        # so prompt height does not grow later.
        return '\n'


class ActegoryValidator(Validator):
    """"""

    def __init__(self, prompt, *args, **kwargs):
        super(ActegoryValidator, self).__init__(*args, **kwargs)
        self.prompt = prompt
        self.update_last_seen()

    def update_last_seen(self):
        # The validator is called with every change to text -- and
        # then once on ENTER/'accept-line' where the text will be
        # the same as we just saw it.
        self.last_text = self.prompt.edit_part_text

    def validate(self, document):
        text = document.text
        last_text = self.last_text

        self.prompt.debug('text: {} / last_text: {}'.format(text, last_text))

        if self.last_text == text:
            # The text has not changed, which can happen when the user
            # types control characters, so just bail now; we already
            # know the score.
            return
        self.last_text = text

        # tl;dr: If user types '@' after activity, lock activity name
        #   and move on to editing the category.
        # (lb): A question I asked myself: Would you rather trigger on the
        # separator (@) being anywhere in the string, or only at the end?
        # - I think it'd be weird to type some text, left arrow back over
        # it, then insert an '@' and have the prompt "lock" the stuff to
        # the left... also, the rest of the code allows '@' in Activity
        # and Category names, so unless we force the user to use the
        # command line so they can "quote @ around" the problem, at least
        # offer a weird little work-around in the prompt, which is:
        #   - If you want to use a separator character ('@') in the Activity
        #   name, type the name first without the separator, then left-arrow
        #   back to where it belongs, and insert it, then hit ENTER to
        #   trigger the prompt to move on to editing the category.
        # - Note that the prompt still does not support the separator
        # character at the end of the Activity name, but there's always
        # the command line, e.g.,:
        #   `dob edit --activity="Foo@" 1234`
        # or
        #   `dob now "Foo@"@`
        # which might look strange unless you follow the cosmic CLI groove.
        # Then it makes complete sense.
        # - Recap: If you put the '@' at the end of the prompt text, the code
        # here interprets it as finishing the Activity name; but if you insert
        # the '@' within the text and not at the end, “why not” [which is
        # something an HIIT coach might say to motivate you, why not. -lb].
        # FIXME/2019-11-24 14:49: Make this behavior optional?
        # FIXME/2019-11-24 14:49: What about sep and tag CONFIG options?
        if not self.prompt.lock_act and text.endswith(self.prompt.sep):
            activity = text.strip(self.prompt.sep)
            self.prompt.lock_activity(activity)

        # Use ValidationError to show message in bottom-left of prompt
        # (just above our the_bottom_area footer).
        # Not so fast: (lb): I think it's a useful message (it makes the prompt
        # less intimidating, I'd argue), but raising an error on every character
        # typed causes the suggestion list to flicker! So just do this for the
        # very first character the user types, then don't bother any more.
        if not last_text:
            if not self.prompt.lock_act:
                message = _('Type `{}` or press ENTER to finish {} name').format(
                    self.prompt.sep, self.prompt.edit_part_type.capitalize()
                )
            else:
                message = _('Type Ctrl-s or press ENTER to finish {} name').format(
                    self.prompt.edit_part_type.capitalize()
                )
            raise ValidationError(message=message, cursor_position=0)

