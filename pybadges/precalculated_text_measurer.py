# Copyright 2018 The pybadge Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Measure the width, in pixels, of a string rendered using DejaVu Sans 110pt.

Uses a precalculated set of metrics to calculate the string length.
"""

import io
import json
import importlib.resources as resources
from typing import cast, Mapping, TextIO, Type

from pybadges import text_measurer


class PrecalculatedTextMeasurer(text_measurer.TextMeasurer):
    """Measures the width of a string using a precalculated set of tables."""

    _default_cache = None

    def __init__(self, default_character_width: float,
                 char_to_width: Mapping[str, float],
                 pair_to_kern: Mapping[str, float]):
        """Initializer for PrecalculatedTextMeasurer.

        Args:
            default_character_width: the average width, in pixels, of a
                character in DejaVu Sans 110pt.
            char_to_width: a mapping between a character and it's width,
                in pixels, in DejaVu Sans 110pt.
            pair_to_kern: a mapping between pairs of characters and the kerning
                distance between them e.g. text_width("IJ") =>
                    (char_to_width["I"] + char_to_width["J"]
                    - pair_to_kern.get("IJ", 0))
        """
        self._default_character_width = default_character_width
        self._char_to_width = char_to_width
        self._pair_to_kern = pair_to_kern

    def text_width(self, text: str) -> float:
        """Returns the width, in pixels, of a string in DejaVu Sans 110pt."""
        width = 0
        for index, c in enumerate(text):
            width += self._char_to_width.get(c, self._default_character_width)
            width -= self._pair_to_kern.get(text[index:index + 2], 0)

        return width

    @staticmethod
    def from_json(f: TextIO) -> 'PrecalculatedTextMeasurer':
        """Return a PrecalculatedTextMeasurer given a JSON stream.

        See precalculate_text.py for details on the required format.
        """
        o = json.load(f)
        return PrecalculatedTextMeasurer(o['mean-character-length'],
                                         o['character-lengths'],
                                         o['kerning-pairs'])

    @classmethod
    def default(cls) -> 'PrecalculatedTextMeasurer':
        """Returns a reasonable default PrecalculatedTextMeasurer."""
        if cls._default_cache is not None:
            return cls._default_cache

        resource_name_xz = 'default-widths.json.xz'
        resource_name_json = 'default-widths.json'

        resource_package = resources.files(__name__)
        resource_xz_path = resource_package / resource_name_xz
        resource_json_path = resource_package / resource_name_json

        if resource_xz_path.exists():
            import lzma
            with resources.as_file(resource_xz_path) as path:
                with lzma.open(path, "rt") as f:
                    cls._default_cache = PrecalculatedTextMeasurer.from_json(cast(TextIO, f))
                    return cls._default_cache
        elif resource_json_path.exists():
            with resources.as_file(resource_json_path) as path:
                with open(path, 'r', encoding='utf-8') as f:
                    cls._default_cache = PrecalculatedTextMeasurer.from_json(f)
                    return cls._default_cache
        else:
            raise ValueError('could not load default-widths.json')
