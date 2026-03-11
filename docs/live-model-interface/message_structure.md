# Message structure

This document describes the RabbitMQ message base fields, routing keys, and payloads used by the live model interface.

## RabbitMQ setup

- Exchange: `EnvSettings.rabbitmq_exchange()` (default `mapeditor.topic`), type `topic`, durable.
- Queue: `EnvSettings.rabbitmq_queue()` (default `mapeditor`).
- App id: `esdl-mapeditor` (set on publish via `BasicProperties.app_id`).
- Content type: `application/json`.
- Timestamps are serialized with `datetime.isoformat()`.

## Type definitions

Message types are defined in `src/tno/live_model_interface/shared/message_types.py`.

## Common base fields (`LmiMessage`)

All messages use the base fields below and add message-specific fields.

```json
{
  "id": "<uuid>",
  "timestamp": "2024-01-02T03:04:05.678901+00:00",
  "client_id": "<session client id or null>",
  "user_email": "<email or null>"
}
```

## Routing keys and payloads

### MapEditor -> Live model interface

- `events.pm.new` (init new project)
  - Initializes a new project in the live model interface with the current active variant.

- `events.pm.add` (add variant + ESDL)
  - Adds a new variant and its ESDL to the live model interface.

- `events.pm.delete` (delete variant)
  - Deletes a variant from the live model interface.

- `events.pm` (full project manager)
  - Sends the full project manager snapshot to the live model interface.

- `events.pm.clear` (clear project manager)
  - Signals that live model interfaces can clear their project managers.

- `events.esdl.high_level_change` (incremental change)
  - Sends a high-level ESDL change for the active variant.

- `{lmi_id}.activation` (activate/deactivate LMI)
  - Activates or deactivates a specific live model interface for a client.

### Live model interface -> MapEditor

The MapEditor subscribes to `lmi.#` on the topic exchange in `src/tno/live_model_interface/lmi_listener.py`.

- `lmi.esdl.high_level_change`
  - Applies a high-level ESDL change to the active variant and triggers UI updates.

- `lmi.pm.refresh`
  - Requests a project manager refresh; if `client_id` is set, only that client is refreshed.

- `events.variant.new`
  - Creates a new variant in the MapEditor based on a parent variant.
  - Note: currently not used.

### Live model interface -> MapEditor (results)

The MapEditor also subscribes to `results.#` in `src/tno/live_model_interface/results_listener.py` and forwards the
payload to the UI via Socket.IO event `results.asset.positioning`.

- `results.*`
  - Type: free-form JSON (no enforced schema in the listener).
  - Example (legacy): `WindPotentialResultMessage` (defined but not currently used in code).

## Message type reference

Field definitions and type names: `src/tno/live_model_interface/shared/message_types.py`.
