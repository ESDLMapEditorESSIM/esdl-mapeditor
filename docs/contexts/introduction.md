# Contexts

Use this section to understand how contexts behave in the ESDL MapEditor and where each context type is configured.
It covers the current behavior only.

## Why contexts

The MapEditor has grown into a large feature set. Contexts help users focus by highlighting the functionality they need
for a specific task while keeping the rest available but less prominent. A context can pre-activate WMS layers, add
context menu actions, or activate workflows so users don't get lost in the options.

## Relation to workflows and view modes

Contexts and workflows are complementary. Workflows guide users through steps; contexts modify the UI and behavior while
those steps are executed. A workflow step can activate a context to enable the tools needed for that task. Unlike a
workflow step, a context can remain active across multiple steps.

View modes already change the UI to modify attributes and shortcuts. We've renamed these to model contexts. A model in
this case is for example ESSIM or CHESS.

## Context types

There are three context levels in the MapEditor. Each level is mutually exclusive within itself.

### Application contexts (high-level flow)

Application contexts represent the overall flow the user is working on. They activate live model interfaces (LMIs) and
provide a descriptive label such as "Ruimtelijke Energie Verkenner".

Implementation info:
- Stored in MongoDB collection `application_contexts` (see `src/tno/mongo/models.py`).
- Available contexts are fetched from `/context/applications`.
- Activation/clearing uses `/context/applications/<application_id>/activate` and `/context/applications/<application_id>/clear`.
- Active application context is stored in the user session and can toggle LMIs.
- The frontend composable lives in `vue/composables/applicationContext.js`.

See `docs/contexts/application-contexts.md` for field-level details and an example.

### Activity contexts (task-level focus)

Activity contexts are narrower, user-facing tasks such as "Place windmills" or "Load ETM data". They can enable WMS
layers, toggle ESDL layers, add context menu actions, show toasts, and optionally open workflows or call a JS function.

Implementation info:
- Stored in MongoDB collection `activity_contexts` (see `src/tno/mongo/models.py`).
- Available contexts are fetched from `/context/activities`.
- Admin management endpoints exist under `/admin/context/activities`.
- The frontend composable lives in `vue/composables/activityContext.js`.

See `docs/contexts/activity-contexts.md` for field-level details and an example.

### Model contexts (model-specific UI)

Model contexts configure the "view mode" for a specific model, affecting the attributes and assets visible in the UI.
Examples are `standard`, `ESSIM`, and `CHESS`.

Implementation info:
- Configured in `src/model_contexts.py`.
- Current mode is stored in the session as `mapeditor_model_context`.
- Frontend uses the socket events `model_contexts_get_mode_info` and `model_contexts_set_mode`.
- Affects attribute categories and the AssetDrawToolbar through `src/asset_draw_toolbar.py`.

## Examples

### Wind turbine placement (activity context)

This example exists as an activity context and shows how to enable a WMS layer plus a map context menu service:

```json
{
  "activity_id": "rve_wind",
  "name": "Place windmills",
  "is_global": true,
  "disable_esdl_layers": [
    "kpi_layer",
    "area_layer"
  ],
  "context_menu_services": [
    {
      "id": "e04ec8d5-a15f-41c4-a8a3-6a94825c9f49",
      "location": "map"
    }
  ],
  "toast_text": "Right click anywhere on the map to place a wind turbine.",
  "wms_layers": [
    "a7399469-e957-4f87-a292-90dd3a07f6a6"
  ]
}
```
