# Renderer Debug Overlay

The human renderer (`pysc2.lib.renderer_human.RendererHuman`) now accepts a
lightweight payload describing the agent's internal state. When enabled, the
viewer paints PPO statistics, curriculum metadata, and spatial diagnostics on
top of the normal RGB/feature panes so you can audit policies without building
custom UIs.

## Wiring the payload

1. Pass a callable to the environment when it is created (only supported when
   `visualize=True` and the environment runs in-process—skip SubprocEnv or other
   wrappers when enabling the overlay):
   ```python
   def build_debug_payload():
     return {
         "metrics": {
             "curriculum_stage": trainer.curriculum_stage,
             "recent_win_rate": tracker.win_rate,
             "ppo_value_loss": stats.value_loss,
         },
         "global_vector": trainer.latest_global_vector.tolist(),
         "spatial_layers": [
             {
                 "name": "build_candidates",
                 "surface": "screen",
                 "points": [
                     {"pos": loc, "radius": 1.25, "label": name}
                     for name, loc in candidate_locations
                 ],
                 "colormap": "candidates",
             },
         ],
     }

   env = sc2_env.SC2Env(
       map_name="Simple64",
       players=[sc2_env.Agent(sc2_env.Race.terran)],
       agent_interface_format=interfaces.AgentInterfaceFormat(
           feature_dimensions=sc2_env.Dimensions(screen=84, minimap=64)),
       visualize=True,
       debug_payload_fn=build_debug_payload,
   )
   ```
   You can also call `env.set_debug_payload_fn(fn)` after construction.
2. Start your usual training or evaluation loop. A dedicated background thread
   (owned by the env) polls the callable roughly every 100 ms, stores the
   snapshot, and the renderer reuses that cache whenever a frame is drawn.
   Nothing is invoked when `visualize=False` or when no renderer exists.

## Payload schema

The payload must be JSON-serializable; `RendererHuman.set_debug_payload`
recursively copies the structure and converts NumPy scalars/arrays into Python
types. All keys are optional:

- `metrics`: dict of scalar values printed in the chrome bar (F6 toggles).
- `scalars`: alternate dict for misc floats/ints if you prefer a different key.
- `global_vector`: list/tuple of floats; only the first few entries are shown.
- `notes`: short descriptive text.
- `spatial_layers`: list of dicts describing overlays that sit on top of a
  surface (`"screen"`, `"minimap"`, `"feature"`, or `"panel"`):
  - `points`: list of markers `{ "pos": [x, y], "radius": 1.0, "label": "CC" }`
    describing circles drawn in world-space map coordinates. Optional `color`,
    `strength`, and `thickness` fields tweak appearance.
  - `heatmap`: 2‑D tensor (list-of-lists) rendered as translucent rectangles on
    the selected surface. Use `bounds: [min_x, min_y, max_x, max_y]` to change
    the world-space area. When `surface == "panel"` the heatmap is drawn inside
    a dedicated mini-panel (appended to the feature-layer grid).
  - `colormap`/`color`: pick from `candidates`, `waypoints`, `heatmap`, or any
    `pysc2.lib.colors` constant.
  - `alpha`: opacity multiplier (defaults to 0.4).

The renderer keeps the last non-`None` payload and never blocks SC2 stepping; if
your supplier is unavailable for a frame simply return `None` and the prior
snapshot will be reused.

## Hotkeys

- `F6`: toggle text overlays (metrics/global vector/notes).
- `F7`: toggle spatial overlays (points/heatmaps).

Toggles persist for the viewer's lifetime and are exposed in the `?` help menu.

## Performance guidelines

- Keep payloads short—only scalars, short lists, or tensors under a few hundred
  cells. Oversized payloads will slow the UI regardless of PySC2 logic.
- Convert tensors to CPU/NumPy arrays before returning them; the renderer copies
  everything to avoid sharing buffers with the learner thread.
- Run overlays in a single in-process env only. Vectorized/SubprocEnv setups
  can't reach the renderer, so skip those wrappers when `debug_payload_fn` is
  supplied.
- If a payload update throws an exception it is logged and ignored so
  experiments keep running.
