"""
title: SparkyFitness Exercise Logger
author: ab
version: 0.1.0
description: Log exercises, search the exercise database, and view workout history via the SparkyFitness REST API.
"""

import requests
import json
from datetime import date, datetime
from zoneinfo import ZoneInfo
from typing import Optional
from pydantic import BaseModel, Field


class Tools:
    class Valves(BaseModel):
        sparky_base_url: str = Field(
            default="http://your-sparkyfitness-server",
            description="Base URL of the SparkyFitness server (no trailing slash)",
        )
        sparky_api_key: str = Field(
            default="",
            description="SparkyFitness API key (Bearer token)",
        )
        equipment_tag_map: str = Field(
            default='{"14": "Chest Press", "7": "Lat Pulldown", "22": "Leg Press"}',
            description='JSON mapping of gym equipment tag numbers to exercise names. Example: {"14": "Chest Press", "7": "Lat Pulldown"}',
        )
        exercise_provider_id: str = Field(
            default="",
            description="UUID of the Free Exercise DB external provider in SparkyFitness.",
        )
        timezone: str = Field(
            default="America/Los_Angeles",
            description="Timezone for date calculations (e.g. America/Los_Angeles, America/New_York). Used when no date is explicitly provided.",
        )

    def __init__(self):
        self.valves = self.Valves()

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.valves.sparky_api_key}",
            "Content-Type": "application/json",
        }

    def _url(self, path: str) -> str:
        return f"{self.valves.sparky_base_url}/api{path}"

    def _today(self) -> str:
        """Get today's date in the configured timezone."""
        tz = ZoneInfo(self.valves.timezone)
        return datetime.now(tz).strftime("%Y-%m-%d")

    def _search_external(self, query: str) -> list:
        """Search the external Free Exercise DB provider."""
        try:
            resp = requests.get(
                self._url("/exercises/search-external"),
                headers=self._headers(),
                params={
                    "query": query,
                    "providerType": "free-exercise-db",
                    "providerId": self.valves.exercise_provider_id,
                },
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException:
            return []

    def _import_external_exercise(self, external_id: str) -> dict | None:
        """Import an exercise from Free Exercise DB into the local database."""
        try:
            resp = requests.post(
                self._url("/freeexercisedb/add"),
                headers=self._headers(),
                json={
                    "exerciseId": external_id,
                    "providerId": self.valves.exercise_provider_id,
                },
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException:
            return None

    async def lookup_equipment_tag(
        self,
        tag_number: str,
    ) -> str:
        """
        Look up a gym equipment tag number to find the exercise name.
        Each machine at the gym has a numbered tag. This resolves that number
        to an exercise name and searches the SparkyFitness database for it.

        :param tag_number: The number on the gym equipment tag (e.g. "14").
        :return: The exercise name mapped to that tag and matching exercises from the database.
        """
        try:
            tag_map = json.loads(self.valves.equipment_tag_map)
        except json.JSONDecodeError:
            return "Error: equipment_tag_map Valve contains invalid JSON. Please fix it in settings."

        exercise_name = tag_map.get(str(tag_number))
        if not exercise_name:
            available = ", ".join(f"#{k} = {v}" for k, v in tag_map.items())
            return (
                f"No exercise mapped to tag #{tag_number}. "
                f"Known tags: {available or 'none configured'}."
            )

        # Search SparkyFitness for this exercise
        try:
            resp = requests.get(
                self._url("/exercises/search"),
                headers=self._headers(),
                params={"searchTerm": exercise_name},
                timeout=15,
            )
            resp.raise_for_status()
            results = resp.json()
            if results:
                matches = []
                for ex in results[:5]:
                    matches.append(
                        f"  - **{ex.get('name')}** (ID: `{ex.get('id')}`) "
                        f"| Equipment: {ex.get('equipment', 'N/A')}"
                    )
                return (
                    f"Tag #{tag_number} \u2192 **{exercise_name}**\n"
                    f"Matching exercises in database:\n" + "\n".join(matches)
                )
            else:
                # Fallback to external search
                ext_results = self._search_external(exercise_name)
                if ext_results:
                    imported = self._import_external_exercise(ext_results[0].get("id"))
                    if imported:
                        return (
                            f"Tag #{tag_number} \u2192 **{exercise_name}**\n"
                            f"Auto-imported: **{imported.get('name')}** (ID: `{imported.get('id')}`)"
                        )
                return (
                    f"Tag #{tag_number} \u2192 **{exercise_name}**, "
                    f"but no matching exercises found locally or externally."
                )
        except requests.exceptions.RequestException as e:
            return f"Tag #{tag_number} \u2192 **{exercise_name}** (database search failed: {e})"

    async def search_exercises(
        self,
        search_term: str,
        equipment_filter: Optional[str] = None,
        muscle_group_filter: Optional[str] = None,
    ) -> str:
        """
        Search the exercise database by name, equipment, or muscle group.
        Use this to find exercise IDs before logging a workout.

        :param search_term: Name or partial name of the exercise to search for.
        :param equipment_filter: Optional comma-separated equipment filter (e.g. "Dumbbell,Barbell").
        :param muscle_group_filter: Optional comma-separated muscle group filter (e.g. "Chest,Biceps").
        :return: JSON list of matching exercises with their IDs and details.
        """
        params = {}
        if search_term:
            params["searchTerm"] = search_term
        if equipment_filter:
            params["equipmentFilter"] = equipment_filter
        if muscle_group_filter:
            params["muscleGroupFilter"] = muscle_group_filter

        try:
            resp = requests.get(
                self._url("/exercises/search"),
                headers=self._headers(),
                params=params,
                timeout=15,
            )
            resp.raise_for_status()
            exercises = resp.json()
            if not exercises:
                # Fallback to external search
                ext_results = self._search_external(search_term)
                if not ext_results:
                    return f"No exercises found matching '{search_term}' locally or externally."
                results = []
                for ex in ext_results[:15]:
                    results.append(
                        f"- **{ex.get('name')}** (External ID: `{ex.get('id')}`) "
                        f"| Equipment: {ex.get('equipment', 'N/A')} "
                        f"| Muscles: {ex.get('primary_muscles', 'N/A')} "
                        f"\u26a1 *Will be auto-imported when logged*"
                    )
                return f"Found {len(ext_results)} exercise(s) from external database:\n" + "\n".join(results)
            results = []
            for ex in exercises[:15]:
                results.append(
                    f"- **{ex.get('name')}** (ID: `{ex.get('id')}`) "
                    f"| Category: {ex.get('category', 'N/A')} "
                    f"| Equipment: {ex.get('equipment', 'N/A')} "
                    f"| Muscles: {ex.get('primary_muscles', 'N/A')}"
                )
            return f"Found {len(exercises)} exercise(s):\n" + "\n".join(results)
        except requests.exceptions.RequestException as e:
            return f"Error searching exercises: {e}"

    async def log_exercise(
        self,
        exercise_name: str,
        num_sets: int,
        reps_per_set: int,
        weight_kg: Optional[float] = None,
        entry_date: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        notes: Optional[str] = None,
        exercise_id: Optional[str] = None,
        sets_data: Optional[str] = None,
    ) -> str:
        """
        Log an exercise entry to SparkyFitness with sets, reps, and weight.
        For uniform sets (same reps/weight each set), use num_sets + reps_per_set + weight_kg.
        For varied sets (different reps/weight per set), provide sets_data JSON instead.

        :param exercise_name: Name of the exercise (used if exercise_id not provided; will search for a match).
        :param num_sets: Number of sets to log (e.g. 3). Ignored if sets_data is provided.
        :param reps_per_set: Number of reps per set (e.g. 10). Ignored if sets_data is provided.
        :param weight_kg: Weight in kilograms per set (e.g. 10.0). Ignored if sets_data is provided.
        :param entry_date: Date in YYYY-MM-DD format. Defaults to today.
        :param duration_minutes: Total duration in minutes (optional).
        :param notes: Optional notes for this entry.
        :param exercise_id: UUID of the exercise (if known). Skips search if provided.
        :param sets_data: Advanced: JSON array of sets for varied reps/weight. Each set: {"reps": number, "weight": number, "set_type": "Working Set"|"Warmup"|"Drop Set"|"Failure"}. Overrides num_sets/reps_per_set/weight_kg if provided.
        :return: Confirmation message with the logged entry details.
        """
        # Resolve exercise_id if not provided
        if not exercise_id:
            try:
                search_resp = requests.get(
                    self._url("/exercises/search"),
                    headers=self._headers(),
                    params={"searchTerm": exercise_name},
                    timeout=15,
                )
                search_resp.raise_for_status()
                results = search_resp.json()
                if results:
                    # Try exact match first
                    exact = [
                        e
                        for e in results
                        if e.get("name", "").lower() == exercise_name.lower()
                    ]
                    exercise_id = (
                        exact[0]["id"] if exact else results[0]["id"]
                    )
                else:
                    # Fallback: search external and auto-import
                    ext_results = self._search_external(exercise_name)
                    if ext_results:
                        # Pick best match
                        best = None
                        for ex in ext_results:
                            if ex.get("name", "").lower() == exercise_name.lower():
                                best = ex
                                break
                        if not best:
                            best = ext_results[0]
                        imported = self._import_external_exercise(best.get("id"))
                        if imported:
                            exercise_id = imported["id"]
                            exercise_name = imported.get("name", exercise_name)
                        else:
                            return f"Found '{best.get('name')}' externally but failed to import it."
                    else:
                        return (
                            f"Exercise '{exercise_name}' not found locally or externally. "
                            f"Please check the name."
                        )
            except requests.exceptions.RequestException as e:
                return f"Error searching for exercise: {e}"

        # Build sets from scalar params or parse sets_data JSON
        if sets_data:
            try:
                sets = json.loads(sets_data) if isinstance(sets_data, str) else sets_data
            except json.JSONDecodeError as e:
                return f"Invalid sets_data JSON: {e}"
        else:
            sets = []
            for i in range(num_sets):
                s = {"reps": reps_per_set}
                if weight_kg is not None:
                    s["weight"] = weight_kg
                sets.append(s)

        # Ensure each set has required set_number and set_type
        for i, s in enumerate(sets):
            if "set_number" not in s:
                s["set_number"] = i + 1
            if "set_type" not in s:
                s["set_type"] = "Working Set"

        # Build payload
        payload = {
            "exercise_id": exercise_id,
            "entry_date": entry_date or self._today(),
            "sets": sets,
        }
        if duration_minutes is not None:
            payload["duration_minutes"] = duration_minutes
        if notes:
            payload["notes"] = notes

        try:
            resp = requests.post(
                self._url("/exercise-entries"),
                headers=self._headers(),
                json=payload,
                timeout=15,
            )
            resp.raise_for_status()
            entry = resp.json()
            set_summary = ", ".join(
                [
                    f"Set {i+1}: {s.get('reps', 0)} reps @ {s.get('weight', 0)}kg"
                    for i, s in enumerate(sets)
                ]
            )
            return (
                f"Logged **{exercise_name}** on {payload['entry_date']}.\n"
                f"Sets: {set_summary}\n"
                f"Entry ID: `{entry.get('id', 'unknown')}`"
            )
        except requests.exceptions.RequestException as e:
            error_detail = ""
            if hasattr(e, "response") and e.response is not None:
                error_detail = f" - {e.response.text}"
            return f"Error logging exercise: {e}{error_detail}"

    async def get_todays_entries(
        self,
        entry_date: Optional[str] = None,
    ) -> str:
        """
        Get all exercise entries logged for a specific date (defaults to today).

        :param entry_date: Date in YYYY-MM-DD format. Defaults to today.
        :return: Summary of exercises logged on that date.
        """
        target_date = entry_date or self._today()

        try:
            resp = requests.get(
                self._url("/exercise-entries/by-date"),
                headers=self._headers(),
                params={"selectedDate": target_date},
                timeout=15,
            )
            resp.raise_for_status()
            entries = resp.json()
            if not entries:
                return f"No exercises logged for {target_date}."

            lines = [f"**Exercise diary for {target_date}** ({len(entries)} entries):"]
            for entry in entries:
                name = entry.get("exercise_name") or entry.get("name", "Unknown")
                sets = entry.get("sets", [])
                if sets:
                    set_details = ", ".join(
                        [
                            f"{s.get('reps', 0)}\u00d7{s.get('weight', 0)}kg"
                            for s in sets
                        ]
                    )
                    lines.append(f"- **{name}**: {set_details}")
                else:
                    reps = entry.get("reps", "")
                    weight = entry.get("weight", "")
                    dur = entry.get("duration_minutes", "")
                    detail = ""
                    if reps:
                        detail += f"{reps} reps"
                    if weight:
                        detail += f" @ {weight}kg"
                    if dur:
                        detail += f" ({dur} min)"
                    lines.append(f"- **{name}**: {detail or 'logged'}")
            return "\n".join(lines)
        except requests.exceptions.RequestException as e:
            return f"Error fetching entries: {e}"

    async def get_exercise_history(
        self,
        exercise_id: str,
        limit: Optional[int] = 10,
    ) -> str:
        """
        Get historical entries for a specific exercise to track progress over time.

        :param exercise_id: The UUID of the exercise to get history for.
        :param limit: Maximum number of history entries to return (default 10).
        :return: Historical exercise entries showing progression.
        """
        try:
            resp = requests.get(
                self._url(f"/exercise-entries/history/{exercise_id}"),
                headers=self._headers(),
                params={"limit": limit},
                timeout=15,
            )
            resp.raise_for_status()
            history = resp.json()
            if not history:
                return "No history found for this exercise."

            lines = [f"**Exercise history** (last {len(history)} sessions):"]
            for entry in history:
                entry_date = entry.get("entry_date", "?")
                if isinstance(entry_date, str) and "T" in entry_date:
                    entry_date = entry_date.split("T")[0]
                sets = entry.get("sets", [])
                if sets:
                    best_set = max(sets, key=lambda s: s.get("weight", 0))
                    set_summary = (
                        f"{len(sets)} sets, best: "
                        f"{best_set.get('reps', 0)}\u00d7{best_set.get('weight', 0)}kg"
                    )
                else:
                    set_summary = f"{entry.get('reps', '?')} reps @ {entry.get('weight', '?')}kg"
                lines.append(f"- {entry_date}: {set_summary}")
            return "\n".join(lines)
        except requests.exceptions.RequestException as e:
            return f"Error fetching history: {e}"

    async def get_available_equipment(self) -> str:
        """
        Get the list of available equipment types in the exercise database.
        Useful for filtering exercises by equipment.

        :return: List of available equipment types.
        """
        try:
            resp = requests.get(
                self._url("/exercises/equipment"),
                headers=self._headers(),
                timeout=15,
            )
            resp.raise_for_status()
            equipment = resp.json()
            return "Available equipment: " + ", ".join(equipment)
        except requests.exceptions.RequestException as e:
            return f"Error fetching equipment: {e}"

    async def get_muscle_groups(self) -> str:
        """
        Get the list of available muscle groups in the exercise database.
        Useful for filtering exercises by muscle group.

        :return: List of available muscle groups.
        """
        try:
            resp = requests.get(
                self._url("/exercises/muscle-groups"),
                headers=self._headers(),
                timeout=15,
            )
            resp.raise_for_status()
            groups = resp.json()
            return "Available muscle groups: " + ", ".join(groups)
        except requests.exceptions.RequestException as e:
            return f"Error fetching muscle groups: {e}"

    async def delete_exercise_entry(
        self,
        entry_id: str,
    ) -> str:
        """
        Delete an exercise entry by its ID.

        :param entry_id: The UUID of the exercise entry to delete.
        :return: Confirmation of deletion.
        """
        try:
            resp = requests.delete(
                self._url(f"/exercise-entries/{entry_id}"),
                headers=self._headers(),
                timeout=15,
            )
            resp.raise_for_status()
            return f"Successfully deleted exercise entry `{entry_id}`."
        except requests.exceptions.RequestException as e:
            return f"Error deleting entry: {e}"
