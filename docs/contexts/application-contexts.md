# Application contexts

Use this page to define and debug application contexts. An application context represents the high-level flow a user
is in and controls which live model interfaces (LMIs) are enabled. Only one application context is active at a time.

## Example

This is a minimal example. The `lmi_id` values must match the live model interface IDs defined in your environment.

```json
{
  "application_id": "rve",
  "name": "Ruimtelijke Energie Verkenner",
  "live_model_interfaces": [
    {
      "lmi_id": "connect-nearest-infra",
      "name": "Connect Nearest Infra",
      "description": "Automatically connect new assets to the transformer of the DSO service area in which the asset is placed",
      "enabled": true,
      "can_be_disabled": true
    }
  ],
  "is_global": false,
  "toast_text": "Ruimtelijke Energie Verkenner context activated"
}
```

## Create or edit application contexts

There is no admin API for application contexts. Use MongoDB directly:

1) Insert or update a document in the `application_contexts` collection.
2) Make the context available to users:
   - Set `is_global: true`, or
   - Add the `application_id` to the user settings `APPLICATION_CONTEXT_IDS`.
3) Reload the MapEditor to refresh the selector list.

Success: the context appears in `GET /context/applications`.

The UI loads contexts from `/context/applications` and activates them via
`/context/applications/<application_id>/activate`.

## Field reference

All fields are optional unless stated otherwise.

- `application_id` (string, required): Unique identifier used for selection and activation.
- `name` (string, required): Label shown in the UI.
- `live_model_interfaces` (object[], required if you want LMIs):
  - `lmi_id` (string, required): Live model interface ID.
  - `name` (string, required): Display name.
  - `description` (string): Shown in the LMI panel.
  - `enabled` (boolean): Initial enabled state.
  - `can_be_disabled` (boolean): If false, the UI checkbox is disabled.
- `is_global` (boolean): If true, the context is visible to all users.
- `toast_text` (string): If present, shown as a toast when the context is activated.
