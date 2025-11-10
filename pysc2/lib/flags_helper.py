"""Utilities for safely reading absl flags before they are parsed."""

from __future__ import annotations

from typing import Any

from absl import flags


def flag_value(name: str, fallback: Any = None) -> Any:
  """Return the current value for `name`, even if absl flags are unparsed.

  Accessing `FLAGS.foo` raises `UnparsedFlagAccessError` until the owning
  application parses argv. Many PySC2 entry points call into library code
  before that happens, so we read the flag object directly and return its
  current `.value`, which absl maintains as the default prior to parsing.
  """
  flag_holder = flags.FLAGS
  try:
    flag = flag_holder[name]
  except KeyError:
    return fallback
  value = getattr(flag, "value", fallback)
  return fallback if value is None else value
