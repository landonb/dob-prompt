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

from prompt_toolkit.layout.processors import AfterInput, BeforeInput, Transformation

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

    @property
    def colors(self):
        return TerrificColors1()

    @property
    def fact_part_friendly(self):
        if self.restrict_category:
            part_name = _('category')
        else:
            # (lb): Just say 'activity', and not
            # the more-correct 'activity@category'.
            part_name = _('activity')
        return part_name

    @property
    def history_topic(self):
        return 'actegory'

    @property
    def type_request(self):
        return _('Enter an Activity@Category')

    def init_completer(self):
        return ActegoryCompleterSuggester(self.summoned)

    def init_processor(self):
        return ActegoryHackyProcessor(self)

    def init_bottombar(self):
        return ActegoryBottomBarArea(self)

    def toggle_restrict_category(self):
        self.restrict_category = not self.restrict_category

    # ***

    def ask_act_cat(self, filter_activity, filter_category):
        self.activity = filter_activity
        self.category = filter_category
        self.restrict_category = False

        if self.activity and not self.category:
            self.restrict_category = True

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
        default = ''
        if self.activity and self.category:
            default = '{}@{}'.format(self.activity, self.category)
        text = self.session_prompt(default=default)
        self.process_user_reponse(text)
        # Prepare to run again, if necessary.
        #  And start with completions open.
        self.processor.start_completion = True
        self.reset_completer()

    def process_user_reponse(self, text):
        if self.restrict_category:
            self.category = text
            # If we prompt again, show activities.
            self.restrict_category = False
        elif '@' in text:
            self.activity, self.category = text.split('@')
            if not self.category:
                # Prepare to prompt again, for category.
                self.restrict_category = True
        else:
            # No '@', so assume just the activity.
            self.activity = text
            # If we prompt again, show categories.
            self.restrict_category = True

    # ***

    def refresh_completions_fact_part(self):
        if self.restrict_category:
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
        if self.restrict_category and '@' in entry:
            _activity_name, category_name = entry.split('@')
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
                name = '{}@{}'.format(item.name, item.category.name)
            except AttributeError:
                pass
        return name


class ActegoryHackyProcessor(HackyProcessor):
    """
    """

    def __init__(self, prompter):
        super(ActegoryHackyProcessor, self).__init__(prompter)
        self.before_input = BeforeInput(text='@')
        self.after_input = AfterInput(text='@')

    def __repr__(self):
        return 'ActegoryHackyProcessor(%r)' % (self.prompter)

    def apply_transformation(self, transformation_input):
        self.mark_summoned(transformation_input)

        if self.prompter.restrict_category:
            text = '{}@'.format(self.prompter.activity)
            self.before_input.text = text
            return self.before_input.apply_transformation(transformation_input)

        if self.prompter.category and not self.prompter.activity:
            text = '@{}'.format(self.prompter.category)
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
        if self.prompter.restrict_category:
            return _('Categories')
        else:
            return _('Activities')

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
        self.prompter.toggle_restrict_category()
        self.prompter.restart_completer(event)

    def extend_bottom(self, _builder, _dummy_section):
        # The Tag prompt adds a line, so add a blank one now,
        # so prompt height does not grow later.
        return '\n'

