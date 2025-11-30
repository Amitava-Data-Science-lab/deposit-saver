import json
import sys
from pathlib import Path
from collections import defaultdict

# ---- input/output ----
# Can be overridden via command line arguments:
# python convert_session_to_eval.py <session_path> [output_path]

SESSION_PATH = Path("./Scripts/sessions/session-6f12200f-99a3-4b8a-a38b-6a2147cd5ab0.json")
OUTPUT_PATH = Path("./Scripts/evals/evalset_multi_turn_test.evalset.json")

# ---- helpers ----

def load_session(path: Path):
    return json.loads(path.read_text())

def group_events_by_invocation(events):
    """Group raw events by invocationId, preserving time order."""
    by_inv = defaultdict(list)
    for ev in events:
        inv_id = ev.get("invocationId")
        if not inv_id:
            continue
        by_inv[inv_id].append(ev)

    # sort each group by timestamp
    for inv_id in by_inv:
        by_inv[inv_id].sort(key=lambda e: e.get("timestamp", 0.0))
    return by_inv

def extract_user_content(inv_events):
    """
    Take the first user-facing message for this invocation.
    Prefer author=='user' & role=='user'.
    """
    for ev in inv_events:
        content = ev.get("content") or {}
        role = content.get("role")
        author = ev.get("author")
        if role == "user" and author == "user":
            return {
                "parts": content.get("parts", []),
                "role": "user",
            }
    # fallback: any role=user content
    for ev in inv_events:
        content = ev.get("content") or {}
        if content.get("role") == "user":
            return {
                "parts": content.get("parts", []),
                "role": "user",
            }
    return None

def extract_final_response(inv_events):
    """
    Last model *text* response for this invocation.
    This should be the final user-facing text, without tool calls.
    If the last text response also has tool calls, separate them out.
    """
    final_parts = None
    for ev in inv_events:
        content = ev.get("content") or {}
        if content.get("role") != "model":
            continue
        parts = content.get("parts") or []

        # consider it a natural-language final response if there's at least one 'text' part
        has_text = any("text" in p for p in parts)

        if has_text:
            # Extract only the text parts (no tool calls)
            text_only_parts = [p for p in parts if "text" in p or "thoughtSignature" in p]
            if text_only_parts:
                final_parts = text_only_parts

    if final_parts is None:
        return None

    return {
        "parts": final_parts,
        "role": "model",
    }

def rename_tool_keys_in_parts(parts):
    """
    ADK evalset uses snake_case:
      - function_call
      - function_response
    Session log uses camelCase:
      - functionCall
      - functionResponse
    """
    new_parts = []
    for p in parts:
        if "functionCall" in p:
            new_parts.append({
                "function_call": p["functionCall"],
                **({k: v for k, v in p.items() if k not in ("functionCall",)})
            })
        elif "functionResponse" in p:
            new_parts.append({
                "function_response": p["functionResponse"],
                **({k: v for k, v in p.items() if k not in ("functionResponse",)})
            })
        else:
            new_parts.append(p)
    return new_parts

def extract_intermediate_data(inv_events):
    """
    Build intermediate_data.invocation_events in the same shape as your sample.
    Only includes events that carry functionCall / functionResponse.
    """
    invocation_events = []

    for ev in inv_events:
        content = ev.get("content") or {}
        parts = content.get("parts") or []

        has_tool = any(("functionCall" in p) or ("functionResponse" in p) for p in parts)
        if not has_tool:
            continue

        # rename keys in parts
        new_parts = rename_tool_keys_in_parts(parts)

        invocation_events.append(
            {
                # sample uses "orchestrator_agent" as author
                "author": "orchestrator_agent",
                "content": {
                    "parts": new_parts,
                    "role": content.get("role", "model"),
                },
            }
        )

    if not invocation_events:
        return {}

    return {
        "invocation_events": invocation_events
    }

def build_conversation(events):
    """
    Convert grouped invocation events into the evalset 'conversation' array.
    """
    by_inv = group_events_by_invocation(events)
    conversation = []

    for inv_id, inv_events in by_inv.items():
        user_content = extract_user_content(inv_events)
        final_response = extract_final_response(inv_events)
        intermediate_data = extract_intermediate_data(inv_events)

        # use earliest timestamp in this invocation
        creation_ts = inv_events[0].get("timestamp", 0.0)

        conv_item = {
            "invocation_id": inv_id,
            "user_content": user_content,
            "intermediate_data": intermediate_data,
            "creation_timestamp": creation_ts,
        }
        if final_response is not None:
            conv_item["final_response"] = final_response

        conversation.append(conv_item)

    # sort conversation by first event timestamp of each invocation
    conversation.sort(key=lambda item: item.get("creation_timestamp", 0.0))
    return conversation

# ---- main ----

def main():
    # Parse command line arguments
    session_path = SESSION_PATH
    output_path = OUTPUT_PATH

    if len(sys.argv) > 1:
        session_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])
    else:
        # Auto-generate output path based on session filename
        if len(sys.argv) > 1:
            session_name = session_path.stem
            output_path = Path(f"./Scripts/evals/evalset_{session_name}.evalset.json")

    session = load_session(session_path)
    session_id = session.get("id", "session")
    app_name = session.get("appName", "mortgage-deposit-agent")
    user_id = session.get("userId", "user")
    events = session.get("events", [])

    conversation = build_conversation(events)

    # use last event timestamp as eval_case creation_timestamp
    last_ts = max((e.get("timestamp", 0.0) for e in events), default=0.0)

    eval_set = {
        "eval_set_id": f"evalset_{session_id}",
        "name": f"evalset_{session_id}",
        "eval_cases": [
            {
                "eval_id": f"case_{session_id}",
                "conversation": conversation,
                "session_input": {
                    "app_name": app_name,
                    "user_id": user_id,
                },
                "creation_timestamp": last_ts,
            }
        ],
        "creation_timestamp": last_ts,
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(eval_set, indent=2))
    print(f"Converted {len(conversation)} conversation turns")
    print(f"Wrote evalset to {output_path.resolve()}")

if __name__ == "__main__":
    main()
