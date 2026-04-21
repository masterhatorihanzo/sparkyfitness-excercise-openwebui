# SparkyFitness Exercise Logger for Open WebUI

An [Open WebUI](https://openwebui.com/) Tool that lets you log gym workouts through natural language conversation. Connects to the [SparkyFitness](https://github.com/arnesborgar/sparky-barcode-scanner) self-hosted fitness tracker via its REST API.

## Features

- **Natural language logging** — _"Log 3 sets of bench press: 10×60kg, 8×65kg, 6×70kg"_
- **Equipment tag lookup** — Resolve gym machine tag numbers to exercises
- **Auto-import** — Exercises not in your local DB are auto-imported from Free Exercise DB
- **Workout history** — View entries by date or exercise progression over time
- **Search** — Find exercises by name, equipment, or muscle group
- **Delete** — Remove incorrect entries

## Mobile App

Open WebUI works great on your phone via [Conduit](https://github.com/cogwheel0/conduit) — a native Open WebUI client for iOS and Android. This enables real-time voice-to-text (STT) workout logging directly from the gym floor.

**Install:**
- [Google Play](https://play.google.com/store/apps/details?id=app.cogwheel.conduit)
- [App Store](https://apps.apple.com/us/app/conduit-open-webui-client/id6749840287)

**Key features for gym use:**
- Voice input — dictate your sets hands-free between exercises
- SSO/OAuth support — works with Authentik, Authelia, Cloudflare Tunnel, Pangolin, and reverse proxy setups
- Home screen widgets — quick-launch a new chat or voice call from the home screen
- Share-sheet integration — share images or text into a prompt

Just connect Conduit to your Open WebUI instance URL, sign in with your existing auth flow, and start logging workouts by voice.

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

## Roadmap

### V2 — QR Codes on Equipment
- **QR code stickers on gym machines** — Scan a QR code on the equipment to auto-identify the exercise instead of remembering machine tag numbers
- Each QR code encodes the exercise name or equipment tag, so you just scan and say "3 sets of 10 at 50kg"
- Eliminates the need for the `equipment_tag_map` valve — the mapping lives on the machine itself
- Could link directly into Conduit or the Open WebUI chat with pre-filled context

### Future Ideas
- Workout templates and routines
- Rep/set suggestions based on history and progression
- Rest timer integration
- Body weight and measurement tracking
- Export workout data (CSV, JSON)

## Requirements

- [Open WebUI](https://openwebui.com/) instance
- [SparkyFitness](https://github.com/arnesborgar/sparky-barcode-scanner) server with API access
- An LLM backend (Ollama, OpenAI-compatible, etc.)

## License

MIT
