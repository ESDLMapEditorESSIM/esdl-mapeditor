# Activity contexts

Use this page to define and debug activity contexts. An activity context is a task-level context such as "Place
windmills" or "Load ETM data". It updates the UI by enabling WMS layers, toggling ESDL layers, and adding context menu
actions. Only one activity context is active at a time.

## Example (wind turbine placement)

This example shows how to enable a WMS layer plus a map context menu service:

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

## Create or edit activity contexts

Pick one of the options below.

### Admin UI

1) Open the admin dialog in the MapEditor.
2) Add or delete activity contexts in the activity contexts panel.
3) Reload the page to refresh the selector list.

Success: the context appears in the activity selector and can be activated.

### Admin API

1) List contexts: `GET /admin/context/activities`.
2) Create a context: `POST /admin/context/activities` with the JSON document.
3) Delete a context: `DELETE /admin/context/activities/<activity_id>`.

Success: the new document is returned by the GET endpoint.

### MongoDB

1) Insert or update a document in the `activity_contexts` collection.
2) Set `is_global: true`, or add the `activity_id` to the user settings entry `ACTIVITY_CONTEXT_IDS`.
3) Reload the MapEditor so the selector refetches contexts.

Success: the context is listed by `GET /context/activities`.

In the future, this should be managed also through application contexts.

## Field reference

All fields are optional unless stated otherwise.

- `activity_id` (string, required): Unique identifier used for selection and admin endpoints.
- `name` (string, required): Label shown in the UI.
- `workflow` (string): Name of a workflow in `window.esdl_services_information` to open when the context is activated.
- `is_global` (boolean): If true, the context is visible to all users.
- `js_function` (string): Name of a global JS function (on `window`) to call on activation. Try to prefer using workflows.
- `wms_layers` (string[]): WMS layer IDs to show when the context is activated.
- `disable_esdl_layers` (string[]): ESDL layer names to hide while the context is active.
- `context_menu_services` (object[]): Adds existing ESDL services to context menus.
  - `id` (string, required): Service ID in `window.esdl_services_information`.
  - `location` (string, required): `map`, `area`, or `building`.
  - `icon` (string): Optional icon used for area menu items.
- `context_menu_js_functions` (object[]): Adds custom JS functions to context menus.
  - `title` (string, required): Menu label.
  - `location` (string, required): `area` is supported; `map` and `building` are not yet implemented.
  - `icon` (string): Icon path.
  - `js_function` (string, required): Name of a global JS function (on `window`).
- `clear_area_context_menu` (boolean): If true, existing area context menu items are temporarily cleared and restored
  when the context is removed.
- `toast_text` (string): Message displayed when the context is activated.
