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
"""Configs for various ways to run starcraft."""

from typing import Optional, Sequence, Tuple

from absl import flags

from pysc2.lib import sc_process
from pysc2.run_configs import platforms
from pysc2.run_configs import lib

flags.DEFINE_string("sc2_run_config", None,
                    "Which run_config to use to spawn the binary.")
FLAGS = flags.FLAGS

_SC2_EXTRA_ARGS: Sequence[str] = ()
_SC2_WINDOW_LOC: Optional[Tuple[int, int]] = None
_SC2_WINDOW_SIZE: Optional[Tuple[int, int]] = None


class _RunConfigProxy(object):
  """Proxy that injects global SC2 launch options."""

  def __init__(self, base_cfg: lib.RunConfig,
               extra_args: Sequence[str],
               window_loc: Optional[Tuple[int, int]],
               window_size: Optional[Tuple[int, int]]):
    self._base = base_cfg
    self._extra_args = list(extra_args)
    self._window_loc = window_loc
    self._window_size = window_size

  def __getattr__(self, item):
    return getattr(self._base, item)

  def start(self, *args, **kwargs):
    extra = list(kwargs.pop("extra_args", []))
    extra.extend(self._extra_args)
    kwargs["extra_args"] = extra
    if self._window_loc is not None and "window_loc" not in kwargs:
      kwargs["window_loc"] = self._window_loc
    if self._window_size is not None and "window_size" not in kwargs:
      kwargs["window_size"] = self._window_size
    return self._base.start(*args, **kwargs)


def _apply_run_config_overrides(cfg: lib.RunConfig) -> lib.RunConfig:
  if (_SC2_EXTRA_ARGS or
      _SC2_WINDOW_LOC is not None or
      _SC2_WINDOW_SIZE is not None):
    return _RunConfigProxy(cfg, _SC2_EXTRA_ARGS, _SC2_WINDOW_LOC, _SC2_WINDOW_SIZE)
  return cfg


def _normalize_window_tuple(
    value: Optional[Sequence[int]],
    label: str) -> Optional[Tuple[int, int]]:
  if value is None:
    return None
  if len(value) != 2:
    raise ValueError("%s must contain exactly two integers" % label)
  return (int(value[0]), int(value[1]))


def set_sc2_extra_args(extra_args: Optional[Sequence[str]]) -> None:
  """Configure additional StarCraft II binary args (e.g., --norender)."""
  global _SC2_EXTRA_ARGS
  _SC2_EXTRA_ARGS = tuple(str(arg) for arg in (extra_args or ()))


def set_sc2_window_config(window_loc: Optional[Sequence[int]],
                          window_size: Optional[Sequence[int]]) -> None:
  """Configure SC2 window placement/size for the next launched client."""
  global _SC2_WINDOW_LOC, _SC2_WINDOW_SIZE
  _SC2_WINDOW_LOC = _normalize_window_tuple(window_loc, "window_loc")
  _SC2_WINDOW_SIZE = _normalize_window_tuple(window_size, "window_size")


def get(version=None):
  """Get the config chosen by the flags."""
  configs = {c.name(): c
             for c in lib.RunConfig.all_subclasses() if c.priority()}

  if not configs:
    raise sc_process.SC2LaunchError("No valid run_configs found.")

  if FLAGS.sc2_run_config is None:  # Find the highest priority as default.
    config_cls = max(configs.values(), key=lambda c: c.priority())
    return _apply_run_config_overrides(config_cls(version=version))

  try:
    return _apply_run_config_overrides(
        configs[FLAGS.sc2_run_config](version=version))
  except KeyError:
    raise sc_process.SC2LaunchError(
        "Invalid run_config. Valid configs are: %s" % (
            ", ".join(sorted(configs.keys()))))
