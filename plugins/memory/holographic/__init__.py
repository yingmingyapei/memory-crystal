"""Memory Crystal — Holographic Memory Plugin for Hermes Agent.

Structured fact storage with entity resolution, trust scoring,
and HRR-based compositional retrieval.

Plugin entry point for Hermes Agent's MemoryProvider interface.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from .store import MemoryStore
from .retrieval import FactRetriever

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool schemas
# ---------------------------------------------------------------------------

FACT_STORE_SCHEMA = {
    "name": "fact_store",
    "description": (
        "Deep structured memory with algebraic reasoning. "
        "Use alongside the memory tool — memory for always-on context, "
        "fact_store for deep recall and compositional queries.\n\n"
        "ACTIONS (simple → powerful):\n"
        "• add — Store a fact the user would expect you to remember.\n"
        "• search — Keyword lookup ('editor config', 'deploy process').\n"
        "• probe — Entity recall: ALL facts about a person/thing.\n"
        "• related — What connects to an entity? Structural adjacency.\n"
        "• reason — Compositional: facts connected to MULTIPLE entities simultaneously.\n"
        "• contradict — Memory hygiene: find facts making conflicting claims.\n"
        "• update/remove/list — CRUD operations.\n\n"
        "IMPORTANT: Before answering questions about the user, ALWAYS probe or reason first."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["add", "search", "probe", "related", "reason", "contradict", "update", "remove", "list"],
            },
            "content": {"type": "string", "description": "Fact content (required for 'add')."},
            "query": {"type": "string", "description": "Search query (required for 'search')."},
            "entity": {"type": "string", "description": "Entity name for 'probe'/'related'."},
            "entities": {"type": "array", "items": {"type": "string"}, "description": "Entity names for 'reason'."},
            "fact_id": {"type": "integer", "description": "Fact ID for 'update'/'remove'."},
            "category": {"type": "string", "enum": ["user_pref", "project", "tool", "general"]},
            "tags": {"type": "string", "description": "Comma-separated tags."},
            "trust_delta": {"type": "number", "description": "Trust adjustment for 'update'."},
            "min_trust": {"type": "number", "description": "Minimum trust filter (default: 0.3)."},
            "limit": {"type": "integer", "description": "Max results (default: 10)."},
        },
        "required": ["action"],
    },
}

FACT_FEEDBACK_SCHEMA = {
    "name": "fact_feedback",
    "description": (
        "Rate a fact after using it. Mark 'helpful' if accurate, 'unhelpful' if outdated. "
        "This trains the memory — good facts rise, bad facts sink."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["helpful", "unhelpful"]},
            "fact_id": {"type": "integer", "description": "The fact ID to rate."},
        },
        "required": ["action", "fact_id"],
    },
}


# ---------------------------------------------------------------------------
# MemoryProvider implementation (abstracted for standalone use)
# ---------------------------------------------------------------------------

class MemoryCrystalProvider:
    """Holographic memory with structured facts, entity resolution, and HRR retrieval.

    Standalone version usable both as a Hermes plugin and as a library.
    """

    def __init__(
        self,
        db_path: str | None = None,
        default_trust: float = 0.5,
        hrr_dim: int = 1024,
        min_trust_threshold: float = 0.3,
        hrr_weight: float = 0.3,
        temporal_decay_half_life: int = 0,
    ):
        self._store = MemoryStore(
            db_path=db_path,
            default_trust=default_trust,
            hrr_dim=hrr_dim,
        )
        self._retriever = FactRetriever(
            store=self._store,
            temporal_decay_half_life=temporal_decay_half_life,
            hrr_weight=hrr_weight,
            hrr_dim=hrr_dim,
        )
        self._min_trust = min_trust_threshold

    @property
    def name(self) -> str:
        return "memory-crystal"

    @property
    def store(self) -> MemoryStore:
        return self._store

    @property
    def retriever(self) -> FactRetriever:
        return self._retriever

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return [FACT_STORE_SCHEMA, FACT_FEEDBACK_SCHEMA]

    def handle_tool_call(self, tool_name: str, args: Dict[str, Any]) -> str:
        if tool_name == "fact_store":
            return self._handle_fact_store(args)
        elif tool_name == "fact_feedback":
            return self._handle_fact_feedback(args)
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    def _handle_fact_store(self, args: dict) -> str:
        try:
            action = args["action"]
            store = self._store
            retriever = self._retriever

            if action == "add":
                fact_id = store.add_fact(
                    args["content"],
                    category=args.get("category", "general"),
                    tags=args.get("tags", ""),
                )
                return json.dumps({"fact_id": fact_id, "status": "added"})

            elif action == "search":
                results = retriever.search(
                    args["query"],
                    category=args.get("category"),
                    min_trust=float(args.get("min_trust", self._min_trust)),
                    limit=int(args.get("limit", 10)),
                )
                return json.dumps({"results": results, "count": len(results)})

            elif action == "probe":
                results = retriever.probe(
                    args["entity"],
                    category=args.get("category"),
                    limit=int(args.get("limit", 10)),
                )
                return json.dumps({"results": results, "count": len(results)})

            elif action == "related":
                results = retriever.related(
                    args["entity"],
                    category=args.get("category"),
                    limit=int(args.get("limit", 10)),
                )
                return json.dumps({"results": results, "count": len(results)})

            elif action == "reason":
                entities = args.get("entities", [])
                if not entities:
                    return json.dumps({"error": "reason requires 'entities' list"})
                results = retriever.reason(
                    entities,
                    category=args.get("category"),
                    limit=int(args.get("limit", 10)),
                )
                return json.dumps({"results": results, "count": len(results)})

            elif action == "contradict":
                results = retriever.contradict(
                    category=args.get("category"),
                    limit=int(args.get("limit", 10)),
                )
                return json.dumps({"results": results, "count": len(results)})

            elif action == "update":
                updated = store.update_fact(
                    int(args["fact_id"]),
                    content=args.get("content"),
                    trust_delta=float(args["trust_delta"]) if "trust_delta" in args else None,
                    tags=args.get("tags"),
                    category=args.get("category"),
                )
                return json.dumps({"updated": updated})

            elif action == "remove":
                removed = store.remove_fact(int(args["fact_id"]))
                return json.dumps({"removed": removed})

            elif action == "list":
                facts = store.list_facts(
                    category=args.get("category"),
                    min_trust=float(args.get("min_trust", 0.0)),
                    limit=int(args.get("limit", 50)),
                )
                return json.dumps({"facts": facts, "count": len(facts)})

            else:
                return json.dumps({"error": f"Unknown action: {action}"})

        except KeyError as exc:
            return json.dumps({"error": f"Missing required argument: {exc}"})
        except Exception as exc:
            return json.dumps({"error": str(exc)})

    def _handle_fact_feedback(self, args: dict) -> str:
        try:
            fact_id = int(args["fact_id"])
            helpful = args["action"] == "helpful"
            result = self._store.record_feedback(fact_id, helpful=helpful)
            return json.dumps(result)
        except KeyError as exc:
            return json.dumps({"error": f"Missing required argument: {exc}"})
        except Exception as exc:
            return json.dumps({"error": str(exc)})

    def system_prompt_block(self) -> str:
        """Return a summary block for system prompt injection."""
        try:
            total = self._store._conn.execute(
                "SELECT COUNT(*) FROM facts"
            ).fetchone()[0]
        except Exception:
            total = 0
        if total == 0:
            return (
                "# Memory Crystal\n"
                "Active. Empty fact store — proactively add facts.\n"
                "Use fact_store and fact_feedback tools."
            )
        return (
            f"# Memory Crystal\n"
            f"Active. {total} facts stored with entity resolution and trust scoring.\n"
            f"Use fact_store to search, probe entities, reason, or add facts.\n"
            f"Use fact_feedback to rate facts after using them."
        )

    def close(self) -> None:
        self._store.close()
