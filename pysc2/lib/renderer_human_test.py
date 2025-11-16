#!/usr/bin/python
# Copyright 2024 Google Inc. All Rights Reserved.
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
"""Tests for renderer_human debug overlay plumbing."""

from absl.testing import absltest
import numpy as np
import pygame

from pysc2.lib import renderer_human


class RendererHumanDebugPayloadTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
    self.renderer = renderer_human.RendererHuman(render_sync=True)

  def tearDown(self):
    self.renderer.close()
    super().tearDown()

  def test_payload_snapshot_persists_when_none_passed(self):
    payload = {"metrics": {"lr": 1e-4}, "global_vector": np.array([1.0, 2.0])}
    self.renderer.set_debug_payload(payload)

    stored = self.renderer._get_debug_payload()

    self.assertIsInstance(stored["global_vector"], list)
    self.assertEqual(stored["metrics"]["lr"], 1e-4)

    # Sending None shouldn't drop the last snapshot.
    self.renderer.set_debug_payload(None)

    self.assertIs(stored, self.renderer._get_debug_payload())

  def test_debug_hotkeys_toggle_flags(self):
    self.assertTrue(self.renderer._debug_metrics_enabled)
    self.assertTrue(self.renderer._debug_layers_enabled)

    self.assertTrue(self.renderer._handle_debug_shortcut(pygame.K_F6))
    self.assertFalse(self.renderer._debug_metrics_enabled)
    self.assertTrue(self.renderer._handle_debug_shortcut(pygame.K_F6))
    self.assertTrue(self.renderer._debug_metrics_enabled)

    self.assertTrue(self.renderer._handle_debug_shortcut(pygame.K_F7))
    self.assertFalse(self.renderer._debug_layers_enabled)

  def test_collect_metrics_respects_toggle(self):
    payload = {"metrics": {"entropy": 1.5}, "notes": "tick"}
    self.renderer.set_debug_payload(payload)

    lines = self.renderer._collect_debug_metric_lines()

    self.assertTrue(any("entropy" in line for line in lines))
    self.renderer._debug_metrics_enabled = False
    self.assertFalse(self.renderer._collect_debug_metric_lines())


if __name__ == "__main__":
  absltest.main()
