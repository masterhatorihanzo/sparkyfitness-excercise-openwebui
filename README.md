# SparkyFitness Exercise Logger for Open WebUI

An [Open WebUI](https://openwebui.com/) Tool that lets you log gym workouts through natural language conversation. Connects to the [SparkyFitness](https://github.com/arnesborgar/sparky-barcode-scanner) self-hosted fitness tracker via its REST API.

## Features

- **Natural language logging** — _"Log 3 sets of bench press: 10×60kg, 8×65kg, 6×70kg"_
- **Equipment tag lookup** — Resolve gym machine tag numbers to exercises
- **Auto-import** — Exercises not in your local DB are auto-imported from Free Exercise DB
- **Workout history** — View entries by date or exercise progression over time
- **Search** — Find exercises by name, equipment, or muscle group
- **Delete** — Remove incorrect entries

## Installation

1. In Open WebUI, go to **Workspace → Tools → Add Tool**
2. Paste the contents of `sparky_exercise_tool.py`
3. Configure the Valves (settings icon on the tool):
   - `sparky_base_url` — Your SparkyFitness server URL
   - `sparky_api_key` — Your API key (Bearer token)
   - `exercise_provider_id` — UUID of the Free Exercise DB provider in your SparkyFitness instance
   - `equipment_tag_map` — JSON mapping of your gym's machine tag numbers to exercise names
   - `timezone` — Your timezone (e.g. `America/Los_Angeles`)

## Usage Examples

In any Open WebUI chat with the tool enabled:

```
Log bench press: 10 reps at 60kg, 8 reps at 65kg, 6 reps at 70kg
What did I log today?
I'm on machine #14, log 3 sets of 10 at 50kg
Show my bench press history
Search for exercises targeting biceps
```

## Data Flow

See [docs/v1-data-flow.md](docs/v1-data-flow.md) for the V1 architecture and data flow documentation.

## Requirements

- [Open WebUI](https://openwebui.com/) instance
- [SparkyFitness](https://github.com/arnesborgar/sparky-barcode-scanner) server with API access
- An LLM backend (Ollama, OpenAI-compatible, etc.)

## License

MIT
