"""Build a conservative handoff from extracted, source-backed observations."""
from handoff import validate_claim

def build_handoff(observations, sources):
    groups = {}
    allowed = {"requested", "open", "completed", "missing_information"}
    for observation in observations:
        checked = validate_claim(observation, sources)
        key = observation.get("task_key")
        state = observation.get("state")
        if not isinstance(key, str) or not key.strip() or state not in allowed:
            raise ValueError("Each observation needs a task key and supported state")
        item = groups.setdefault(key, {"task_key": key, "observations": [], "states": set()})
        item["observations"].append({**checked, "state": state})
        item["states"].add(state)
    output = []
    for key in sorted(groups):
        item = groups[key]
        states = item.pop("states")
        # No timestamp-based silent resolution: completion may refer to a
        # different intervention. Until reviewed, preserve conflicting reports.
        if "completed" in states and states & {"open", "requested", "missing_information"}:
            item["attention"] = "conflicting_reports"
        elif "missing_information" in states:
            item["attention"] = "information_needed"
        elif "completed" in states:
            item["attention"] = "completion_reported"
        else:
            item["attention"] = "open_work"
        item["status"] = "needs_human_review"
        output.append(item)
    return output
