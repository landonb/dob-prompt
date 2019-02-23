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

from .colors_terrific import TerrificColors2
from .hacky_processor import HackyProcessor
from .interface_bonds import KeyBond
from .parts_suggester import FactPartCompleterSuggester
from .sophisti_prompt import SophisticatedPrompt
from .the_bottom_area import BottomBarArea

__all__ = (
    'PromptForMoreTags',
    # Private:
    #   'TagCloudBottomBarArea',
)


class PromptForMoreTags(SophisticatedPrompt):
    """
    """

    def __init__(self, controller):
        super(PromptForMoreTags, self).__init__(controller)
        self.activity = None
        self.tags_cache = {}

    @property
    def activity_name(self):
        if self.activity is None:
            return '<None>'
        else:
            return self.activity.name

    @property
    def category_name(self):
        if self.activity is None:
            return '<Act:None>'
        elif self.activity.category is None:
            return '<None>'
        else:
            return self.activity.category.name

    @property
    def colors(self):
        return TerrificColors2()

    @property
    def fact_part_friendly(self):
        return 'tag'

    @property
    def history_topic(self):
        return 'meta_tag'

    @property
    def type_request(self):
        return _('Select <#tags> for “{}@{}”').format(
            self.activity_name, self.category_name,
        )

    @property
    def completion_hints(self):
        tags_hints = [
            'Type or choose tags and press ENTER to add/remove.'
            ' ENTER empty tag to finish.',
        ]
        tags_hints += super(PromptForMoreTags, self).completion_hints
        return tags_hints

    def init_completer(self):
        return FactPartCompleterSuggester(self.summoned)

    def init_processor(self):
        return HackyProcessor(self)

    def init_bottombar(self):
        return TagCloudBottomBarArea(self)

    def fetch_results(self):
        if self.active_sort == self.bottombar.meta_sort_by_selected:
            results = self.refresh_completions_selected()
        else:
            results = super(PromptForMoreTags, self).fetch_results()
        return results

    def refresh_completions_selected(self):
        results = []
        for tag_name in self.ordered_tags:
            result = SophisticatedPrompt.FakeUsageResult(tag_name, None, None)
            results.append(SophisticatedPrompt.FakeUsageWrapper(result, None, None))
        if self.sort_order == 'desc':
            results.reverse()
        return results

    def ask_for_tags(self, already_selected, activity):
        self.selected_tags = set(tag.name for tag in already_selected)
        self.ordered_tags = list(self.selected_tags)
        self.ordered_tags.sort()

        self.activity = activity

        self.prepare_session()

        self.keep_prompting_until_satisfied()

        return self.selected_tags

    def keep_prompting_until_satisfied(self):
        try:
            self.prompt_for_tags()
        finally:
            self.clean_up_print_text_header()

    def prompt_for_tags(self):
        keep_asking = True
        while keep_asking:
            keep_asking = self.prompt_for_tag()
            # If we prompt again, start with suggestions showing.
            self.processor.start_completion = True
            self.reset_completer()

    def prompt_for_tag(self):
        keep_asking = True
        text = self.session_prompt()
        if text:
            self.process_user_response(text)
        else:
            keep_asking = False
        return keep_asking

    def process_user_response(self, text):
        # Toggle: If not added, add tag; otherwise, remove.
        if text not in self.selected_tags:
            self.selected_tags.add(text)
            self.ordered_tags.append(text)
        else:
            self.selected_tags.remove(text)
            self.ordered_tags.remove(text)

    def refresh_completions_fact_part(self):
        activity = self.refresh_restrict_activity()
        category = self.refresh_restrict_category()
        results = self.tags_get_all(activity, category)
        results = self.remove_selected_from_completions(results)
        return results

    def tags_get_all(self, activity, category):
        # (lb): Using a tags cache makes the interface noticeably more
        # responsive for me (against my Hamster db with 10K+ entries).
        # I don't notice the activity and category cache, so much.
        cache_key = (activity, category, self.active_sort.action, self.sort_order)
        if cache_key in self.tags_cache:
            return self.tags_cache[cache_key]

        results = self.controller.tags.get_all(
            include_usage=True,
            activity=activity,
            category=category,
            sort_col=self.active_sort.action,
            sort_order=self.sort_order,
        )
        self.tags_cache[cache_key] = results
        return results

    def refresh_restrict_activity(self):
        activity = False
        if not self.activity:
            assert(False)  # Need actegory before tags, eh?
            return activity
        act_restrict = TagCloudBottomBarArea.TOGGLE_TYPES[
            TagCloudBottomBarArea.RESTRICT_ACT
        ]
        if self.bottombar.restrict_type == act_restrict:
            activity = self.activity
        return activity

    def refresh_restrict_category(self):
        category = False
        if not self.activity:
            assert(False)  # Need actegory before tags, eh?
            return category
        cat_restrict = TagCloudBottomBarArea.TOGGLE_TYPES[
            TagCloudBottomBarArea.RESTRICT_CAT
        ]
        if self.bottombar.restrict_type == cat_restrict:
            category = self.activity.category
        return category

    def remove_selected_from_completions(self, results):
        culled = []
        for result in results:
            if result[0].name in self.selected_tags:
                continue
            culled.append(result)
        return culled


class TagCloudBottomBarArea(BottomBarArea):
    """
    """

    TOGGLE_TYPES = [_('all'), _('act'), _('cat')]
    RESTRICT_ALL = 0
    RESTRICT_ACT = 1
    RESTRICT_CAT = 2

    def __init__(self, prompter):
        super(TagCloudBottomBarArea, self).__init__(prompter)
        self.restrict_type = TagCloudBottomBarArea.TOGGLE_TYPES[0]

    @property
    def say_types(self):
        return _('Tags')

    @property
    def sort_binding_meta(self):
        sort_bindings = super(TagCloudBottomBarArea, self).sort_binding_meta
        sort_bindings.append(self.meta_sort_by_selected)
        return sort_bindings

    @property
    def meta_sort_by_selected(self):
        # NOTE: Need to specify 'action', or binding won't get applied
        #       (because parent class logic). So using dummy, 'selected'.
        #       (lb): We don't use action callback, but do special check in
        #       fetch_results, which is sorta lame (coupling) but it works.
        return KeyBond(
            'f8',
            _('selected'),
            action='selected',
            highlight=self.meta_sort_highlight,
            briefs=[_('selected')],
            wordy=_('{types} you have selected'),
            sort_order='asc',
        )

    def init_hooks_filter(self):
        def brief_scope(binding):
            return self.restrict_type

        # Option to toggle between filtering tags by acts, cats, or neither.
        self.filter_bindings = [
            KeyBond(
                'f9',
                brief_scope,
                self.toggle_scope,
                briefs=TagCloudBottomBarArea.TOGGLE_TYPES,
                highlight=True,
            ),
        ]

    def toggle_scope(self, event):
        curr = TagCloudBottomBarArea.TOGGLE_TYPES.index(self.restrict_type)
        curr = (curr + 1) % len(TagCloudBottomBarArea.TOGGLE_TYPES)
        self.restrict_type = TagCloudBottomBarArea.TOGGLE_TYPES[curr]
        self.prompter.restart_completer(event)

    def extend_bottom(self, _builder, dummy_section):
        parts = []
        parts.append(('', '\n'))
        self.extend_bottom_tagged(parts, dummy_section)
        return parts

    def extend_bottom_tagged(self, parts, dummy_section):
        if not self.prompter.ordered_tags:
            return
        dummy_section.add_zinger(_('Selected: '))
        self.extend_bottom_tag_names(dummy_section)
        self.extend_bottom_truncate_names(dummy_section)
        parts += dummy_section.parts

    def extend_bottom_tag_names(self, dummy_section):
        for tag_name in self.prompter.ordered_tags:
            dummy_section.add_normal(_('#'))
            dummy_section.add_zinger(tag_name)
            dummy_section.add_normal(_(' '))

    def extend_bottom_truncate_names(self, dummy_section):
        term_width = self.prompter.get_size()[1]
        dummy_section.truncate(term_width, _(' <See all with [F8]>'))

