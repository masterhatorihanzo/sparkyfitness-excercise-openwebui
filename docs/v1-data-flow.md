# SparkyFitness Exercise Logger — V1 Data Flow

## Overview

The SparkyFitness Exercise Logger is an [Open WebUI](https://openwebui.com/) Tool that lets users log gym workouts through natural language conversation with an LLM. The tool connects Open WebUI to the SparkyFitness REST API.

## Architecture

```
┌─────────────────────┐
│   User (chat UI)    │
│   Open WebUI        │
└────────┬────────────┘
         │ natural language
         ▼
┌─────────────────────┐
│   LLM (Ollama /     │
│   OpenAI-compat)    │
└────────┬────────────┘
         │ tool calls
         ▼
┌─────────────────────────────────────┐
│  sparky_exercise_tool.py            │
│  (Open WebUI Tool — runs in OWUI)   │
│                                     │
│  Valves (user-configurable):        │
│  • sparky_base_url                  │
│  • sparky_api_key                   │
│  • equipment_tag_map                │
│  • exercise_provider_id             │
│  • timezone                         │
└────────┬────────────────────────────┘
         │ REST API calls (Bearer token auth)
         ▼
┌─────────────────────────────────────┐
│  SparkyFitness Server               │
│  (self-hosted fitness tracker)      │
│                                     │
│  Endpoints used:                    │
│  • GET  /api/exercises/search       │
│  • GET  /api/exercises/search-ext.  │
│  • POST /api/freeexercisedb/add     │
│  • POST /api/exercise-entries       │
│  • GET  /api/exercise-entries/by-d. │
│  • GET  /api/exercise-entries/hist. │
│  • DEL  /api/exercise-entries/:id   │
│  • GET  /api/exercises/equipment    │
│  • GET  /api/exercises/muscle-grps  │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Free Exercise DB                   │
│  (external exercise provider)       │
│  Searched as fallback when local    │
│  DB has no match; auto-imported     │
│  on first use.                      │
└─────────────────────────────────────┘
```

## Data Flow — Logging an Exercise

1. **User says** (in Open WebUI chat): _"Log 3 sets of bench press: 10×60kg, 8×65kg, 6×70kg"_
2. **LLM parses** the request and calls `log_exercise(exercise_name="Bench Press", sets_data='[{"reps":10,"weight":60},{"reps":8,"weight":65},{"reps":6,"weight":70}]')`
3. **Tool searches** SparkyFitness local DB: `GET /api/exercises/search?searchTerm=Bench+Press`
4. **If not found locally**, tool searches external Free Exercise DB: `GET /api/exercises/search-external?query=Bench+Press`
5. **If found externally**, auto-imports: `POST /api/freeexercisedb/add`
6. **Logs the entry**: `POST /api/exercise-entries` with exercise ID, date, and sets array
7. **Returns confirmation** to the LLM, which presents it to the user

## Data Flow — Equipment Tag Lookup

1. **User says**: _"I'm on machine #14, log 3×10 at 50kg"_
2. **LLM calls** `lookup_equipment_tag(tag_number="14")`
3. **Tool resolves** tag via `equipment_tag_map` Valve: `#14 → Chest Press`
4. **Tool searches** SparkyFitness for "Chest Press"
5. **LLM then calls** `log_exercise()` with the resolved exercise

## Tool Functions (V1)

| Function | Purpose |
|---|---|
| `lookup_equipment_tag` | Resolve gym machine tag # → exercise name |
| `search_exercises` | Search by name, equipment, or muscle group |
| `log_exercise` | Log sets/reps/weight for an exercise |
| `get_todays_entries` | View all exercises logged for a date |
| `get_exercise_history` | View historical entries for an exercise |
| `get_available_equipment` | List equipment types in the DB |
| `get_muscle_groups` | List muscle groups in the DB |
| `delete_exercise_entry` | Delete an exercise entry by ID |

## Configuration (Valves)

All configuration is done through Open WebUI's Valve system (per-user settings):

| Valve | Description |
|---|---|
| `sparky_base_url` | SparkyFitness server URL |
| `sparky_api_key` | Bearer token for API auth |
| `equipment_tag_map` | JSON map of machine tag numbers to exercise names |
| `exercise_provider_id` | UUID of the Free Exercise DB provider |
| `timezone` | Timezone for "today" calculations |

## Key Design Decisions

- **Fallback chain**: Local DB → External DB → Auto-import. Users never need to manually add exercises.
- **Equipment tags**: Gym machines have numbered tags. The mapping is configurable per-user via Valves.
- **Timezone-aware**: "Today" respects the user's configured timezone, not the server's.
- **Stateless tool**: No local state; all data lives in SparkyFitness. The tool is purely a REST client.
