# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""PySC2 module: https://github.com/deepmind/pysc2 ."""

import os
import random
from typing import Callable, MutableSequence, Optional, TypeVar

from absl import flags

_T = TypeVar("_T")


def _legacy_shuffle(seq: MutableSequence[_T], rand_fn: Callable[[], float]) -> None:
  for i in range(len(seq) - 1, 0, -1):
    j = int(rand_fn() * (i + 1))
    seq[i], seq[j] = seq[j], seq[i]


def _patch_random_shuffle() -> None:
  """Re-introduce the optional `random` argument removed in Python 3.11."""
  try:
    random.shuffle([0, 1], lambda: 0.5)
  except TypeError:
    original_shuffle = random.shuffle

    def shuffle(seq: MutableSequence[_T],
                rand_fn: Optional[Callable[[], float]] = None) -> None:
      if rand_fn is None:
        original_shuffle(seq)
      else:
        _legacy_shuffle(seq, rand_fn)

    random.shuffle = shuffle  # type: ignore[assignment]


def _ensure_absl_flags_parsed() -> None:
  """Call absl's flags parser if the caller has not done so yet."""
  flags_obj = flags.FLAGS
  is_parsed = getattr(flags_obj, "is_parsed", None)
  if callable(is_parsed) and is_parsed():
    return
  # The module name is irrelevant; we just need any argv-like iterable.
  flags_obj([__name__])


_patch_random_shuffle()
_ensure_absl_flags_parsed()


def load_tests(loader, standard_tests, unused_pattern):
  """Our tests end in `_test.py`, so need to override the test discovery."""
  this_dir = os.path.dirname(__file__)
  package_tests = loader.discover(start_dir=this_dir, pattern="*_test.py")
  standard_tests.addTests(package_tests)
  return standard_tests
