"""Hybrid keyword/BM25 retrieval for Memory Crystal.

Combines FTS5 full-text search with Jaccard similarity reranking,
HRR vector similarity, and trust-weighted scoring.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .store import MemoryStore

try:
    from . import holographic as hrr
except ImportError:
    import holographic as hrr  # type: ignore[no-redef]


class FactRetriever:
    """Multi-strategy fact retrieval with trust-weighted scoring."""

    def __init__(
        self,
        store: MemoryStore,
        temporal_decay_half_life: int = 0,  # days, 0 = disabled
        fts_weight: float = 0.4,
        jaccard_weight: float = 0.3,
        hrr_weight: float = 0.3,
        hrr_dim: int = 1024,
    ):
        self.store = store
        self.half_life = temporal_decay_half_life
        self.hrr_dim = hrr_dim

        # Auto-redistribute weights if numpy unavailable
        if hrr_weight > 0 and not hrr._HAS_NUMPY:
            fts_weight = 0.6
            jaccard_weight = 0.4
            hrr_weight = 0.0

        self.fts_weight = fts_weight
        self.jaccard_weight = jaccard_weight
        self.hrr_weight = hrr_weight

    def search(
        self,
        query: str,
        category: str | None = None,
        min_trust: float = 0.3,
        limit: int = 10,
    ) -> list[dict]:
        """Hybrid search: FTS5 candidates -> Jaccard rerank -> trust weighting.

        Pipeline:
        1. FTS5 search: Get limit*3 candidates from SQLite full-text search
        2. Jaccard boost: Token overlap between query and fact content
        3. Trust weighting: final_score = relevance * trust_score
        4. Temporal decay (optional): decay = 0.5^(age_days / half_life)

        Returns list of dicts with fact data + 'score' field, sorted by score desc.
        """
        # Stage 1: Get FTS5 candidates (more than limit for reranking headroom)
        candidates = self._fts_candidates(query, category, min_trust, limit * 3)

        if not candidates:
            return []

        # Stage 2: Rerank with Jaccard + trust + optional decay
        query_tokens = self._tokenize(query)
        scored = []

        for fact in candidates:
            content_tokens = self._tokenize(fact["content"])
            tag_tokens = self._tokenize(fact.get("tags", ""))
            all_tokens = content_tokens | tag_tokens

            jaccard = self._jaccard_similarity(query_tokens, all_tokens)
            fts_score = fact.get("fts_rank", 0.0)

            # HRR similarity
            if self.hrr_weight > 0 and fact.get("hrr_vector"):
                fact_vec = hrr.bytes_to_phases(fact["hrr_vector"])
                query_vec = hrr.encode_text(query, self.hrr_dim)
                hrr_sim = (hrr.similarity(query_vec, fact_vec) + 1.0) / 2.0  # shift to [0,1]
            else:
                hrr_sim = 0.5  # neutral

            # Combine FTS5 + Jaccard + HRR
            relevance = (self.fts_weight * fts_score
                        + self.jaccard_weight * jaccard
                        + self.hrr_weight * hrr_sim)

            # Trust weighting
            score = relevance * fact["trust_score"]

            # Optional temporal decay
            if self.half_life > 0:
                score *= self._temporal_decay(fact.get("updated_at") or fact.get("created_at"))

            fact["score"] = score
            scored.append(fact)

        # Sort by score descending, return top limit
        scored.sort(key=lambda x: x["score"], reverse=True)
        results = scored[:limit]
        # Strip raw HRR bytes — callers expect JSON-serializable dicts
        for fact in results:
            fact.pop("hrr_vector", None)
        return results

    def probe(
        self,
        entity: str,
        category: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """Compositional entity query using HRR algebra.

        Unbinds entity from memory bank to extract associated content.
        This is NOT keyword search — it uses algebraic structure to find facts
        where the entity plays a structural role.

        Falls back to FTS5 search if numpy unavailable.
        """
        if not hrr._HAS_NUMPY:
            return self.search(entity, category=category, limit=limit)

        conn = self.store._conn
        role_entity = hrr.encode_atom("__hrr_role_entity__", self.hrr_dim)
        entity_vec = hrr.encode_atom(entity.lower(), self.hrr_dim)
        probe_key = hrr.bind(entity_vec, role_entity)

        # Try category-specific bank first, then all facts
        if category:
            bank_name = f"cat:{category}"
            bank_row = conn.execute(
                "SELECT vector FROM memory_banks WHERE bank_name = ?",
                (bank_name,),
            ).fetchone()
            if bank_row:
                bank_vec = hrr.bytes_to_phases(bank_row["vector"])
                extracted = hrr.unbind(bank_vec, probe_key)
                return self._score_facts_by_vector(
                    extracted, category=category, limit=limit
                )

        # Score against individual fact vectors directly
        where = "WHERE hrr_vector IS NOT NULL"
        params: list = []
        if category:
            where += " AND category = ?"
            params.append(category)

        rows = conn.execute(
            f"""
            SELECT fact_id, content, category, tags, trust_score,
                   retrieval_count, helpful_count, created_at, updated_at,
                   hrr_vector
            FROM facts
            {where}
            """,
            params,
        ).fetchall()

        if not rows:
            return self.search(entity, category=category, limit=limit)

        scored = []
        for row in rows:
            fact = dict(row)
            fact_vec = hrr.bytes_to_phases(fact.pop("hrr_vector"))
            residual = hrr.unbind(fact_vec, probe_key)
            role_content = hrr.encode_atom("__hrr_role_content__", self.hrr_dim)
            content_vec = hrr.bind(hrr.encode_text(fact["content"], self.hrr_dim), role_content)
            sim = hrr.similarity(residual, content_vec)
            fact["score"] = (sim + 1.0) / 2.0 * fact["trust_score"]
            scored.append(fact)

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]

    def related(
        self,
        entity: str,
        category: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """Discover facts that share structural connections with an entity.

        Unlike probe (which finds facts *about* an entity), related finds
        facts that are connected through shared context — e.g., other entities
        mentioned alongside this one, or content that overlaps structurally.

        Falls back to FTS5 search if numpy unavailable.
        """
        if not hrr._HAS_NUMPY:
            return self.search(entity, category=category, limit=limit)

        conn = self.store._conn
        entity_vec = hrr.encode_atom(entity.lower(), self.hrr_dim)

        where = "WHERE hrr_vector IS NOT NULL"
        params: list = []
        if category:
            where += " AND category = ?"
            params.append(category)

        rows = conn.execute(
            f"""
            SELECT fact_id, content, category, tags, trust_score,
                   retrieval_count, helpful_count, created_at, updated_at,
                   hrr_vector
            FROM facts
            {where}
            """,
            params,
        ).fetchall()

        if not rows:
            return self.search(entity, category=category, limit=limit)

        scored = []
        role_entity = hrr.encode_atom("__hrr_role_entity__", self.hrr_dim)
        role_content = hrr.encode_atom("__hrr_role_content__", self.hrr_dim)

        for row in rows:
            fact = dict(row)
            fact_vec = hrr.bytes_to_phases(fact.pop("hrr_vector"))
            residual = hrr.unbind(fact_vec, entity_vec)
            entity_role_sim = hrr.similarity(residual, role_entity)
            content_role_sim = hrr.similarity(residual, role_content)
            best_sim = max(entity_role_sim, content_role_sim)
            fact["score"] = (best_sim + 1.0) / 2.0 * fact["trust_score"]
            scored.append(fact)

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]

    def reason(
        self,
        entities: list[str],
        category: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """Multi-entity compositional query — vector-space JOIN.

        Given multiple entities, algebraically intersects their structural
        connections to find facts related to ALL of them simultaneously.
        This is compositional reasoning that no embedding DB can do.

        Falls back to FTS5 search if numpy unavailable.
        """
        if not hrr._HAS_NUMPY or not entities:
            query = " ".join(entities)
            return self.search(query, category=category, limit=limit)

        conn = self.store._conn
        role_entity = hrr.encode_atom("__hrr_role_entity__", self.hrr_dim)

        entity_residuals = []
        for entity in entities:
            entity_vec = hrr.encode_atom(entity.lower(), self.hrr_dim)
            probe_key = hrr.bind(entity_vec, role_entity)
            entity_residuals.append(probe_key)

        where = "WHERE hrr_vector IS NOT NULL"
        params: list = []
        if category:
            where += " AND category = ?"
            params.append(category)

        rows = conn.execute(
            f"""
            SELECT fact_id, content, category, tags, trust_score,
                   retrieval_count, helpful_count, created_at, updated_at,
                   hrr_vector
            FROM facts
            {where}
            """,
            params,
        ).fetchall()

        if not rows:
            query = " ".join(entities)
            return self.search(query, category=category, limit=limit)

        role_content = hrr.encode_atom("__hrr_role_content__", self.hrr_dim)
        scored = []

        for row in rows:
            fact = dict(row)
            fact_vec = hrr.bytes_to_phases(fact.pop("hrr_vector"))

            entity_scores = []
            for probe_key in entity_residuals:
                residual = hrr.unbind(fact_vec, probe_key)
                sim = hrr.similarity(residual, role_content)
                entity_scores.append(sim)

            min_sim = min(entity_scores)
            fact["score"] = (min_sim + 1.0) / 2.0 * fact["trust_score"]
            scored.append(fact)

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]

    def contradict(
        self,
        category: str | None = None,
        threshold: float = 0.3,
        limit: int = 10,
    ) -> list[dict]:
        """Find potentially contradictory facts via entity overlap + content divergence.

        Two facts contradict when they share entities (same subject) but have
        low content-vector similarity (different claims).

        Falls back to empty list if numpy unavailable.
        """
        if not hrr._HAS_NUMPY:
            return []

        conn = self.store._conn

        where = "WHERE f.hrr_vector IS NOT NULL"
        params: list = []
        if category:
            where += " AND f.category = ?"
            params.append(category)

        rows = conn.execute(
            f"""
            SELECT f.fact_id, f.content, f.category, f.tags, f.trust_score,
                   f.created_at, f.updated_at, f.hrr_vector
            FROM facts f
            {where}
            """,
            params,
        ).fetchall()

        if len(rows) < 2:
            return []

        # Guard against O(n^2) explosion on large fact stores
        _MAX_CONTRADICT_FACTS = 500
        if len(rows) > _MAX_CONTRADICT_FACTS:
            rows = sorted(rows, key=lambda r: r["updated_at"] or r["created_at"], reverse=True)
            rows = rows[:_MAX_CONTRADICT_FACTS]

        # Build entity sets per fact
        fact_entities: dict[int, set[str]] = {}
        for row in rows:
            fid = row["fact_id"]
            entity_rows = conn.execute(
                """
                SELECT e.name FROM entities e
                JOIN fact_entities fe ON fe.entity_id = e.entity_id
                WHERE fe.fact_id = ?
                """,
                (fid,),
            ).fetchall()
            fact_entities[fid] = {r["name"].lower() for r in entity_rows}

        facts = [dict(r) for r in rows]
        contradictions = []

        for i in range(len(facts)):
            for j in range(i + 1, len(facts)):
                f1, f2 = facts[i], facts[j]
                ents1 = fact_entities.get(f1["fact_id"], set())
                ents2 = fact_entities.get(f2["fact_id"], set())

                if not ents1 or not ents2:
                    continue

                entity_overlap = len(ents1 & ents2) / len(ents1 | ents2) if (ents1 | ents2) else 0.0
                if entity_overlap < 0.3:
                    continue

                v1 = hrr.bytes_to_phases(f1["hrr_vector"])
                v2 = hrr.bytes_to_phases(f2["hrr_vector"])
                content_sim = hrr.similarity(v1, v2)

                contradiction_score = entity_overlap * (1.0 - (content_sim + 1.0) / 2.0)

                if contradiction_score >= threshold:
                    f1_clean = {k: v for k, v in f1.items() if k != "hrr_vector"}
                    f2_clean = {k: v for k, v in f2.items() if k != "hrr_vector"}
                    contradictions.append({
                        "fact_a": f1_clean,
                        "fact_b": f2_clean,
                        "entity_overlap": round(entity_overlap, 3),
                        "content_similarity": round(content_sim, 3),
                        "contradiction_score": round(contradiction_score, 3),
                        "shared_entities": sorted(ents1 & ents2),
                    })

        contradictions.sort(key=lambda x: x["contradiction_score"], reverse=True)
        return contradictions[:limit]

    def _score_facts_by_vector(
        self,
        target_vec: "np.ndarray",
        category: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """Score facts by similarity to a target vector."""
        conn = self.store._conn

        where = "WHERE hrr_vector IS NOT NULL"
        params: list = []
        if category:
            where += " AND category = ?"
            params.append(category)

        rows = conn.execute(
            f"""
            SELECT fact_id, content, category, tags, trust_score,
                   retrieval_count, helpful_count, created_at, updated_at,
                   hrr_vector
            FROM facts
            {where}
            """,
            params,
        ).fetchall()

        scored = []
        for row in rows:
            fact = dict(row)
            fact_vec = hrr.bytes_to_phases(fact.pop("hrr_vector"))
            sim = hrr.similarity(target_vec, fact_vec)
            fact["score"] = (sim + 1.0) / 2.0 * fact["trust_score"]
            scored.append(fact)

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]

    def _fts_candidates(
        self,
        query: str,
        category: str | None,
        min_trust: float,
        limit: int,
    ) -> list[dict]:
        """Get raw FTS5 candidates from the store with prefix-based query building.

        Two-stage retrieval:
        1. FTS5 MATCH with prefix wildcards (fast for English/Latin terms)
        2. LIKE '%term%' fallback for Chinese terms (FTS5 unicode61 can't segment CJK)

        Returns list of fact dicts with 'fts_rank' field normalized to [0, 1].
        """
        conn = self.store._conn

        # Stage 1: Try FTS5 with prefix matching
        fts_query = self._build_fts_query(query)
        params: list = []
        where_clauses = ["facts_fts MATCH ?"]
        params.append(fts_query)

        if category:
            where_clauses.append("f.category = ?")
            params.append(category)

        params.append(min_trust)
        params.append(limit)

        sql = f"""
            SELECT f.fact_id, f.content, f.category, f.tags,
                   f.trust_score, f.retrieval_count, f.helpful_count,
                   f.created_at, f.updated_at,
                   f.hrr_vector, fts.rank as fts_rank
            FROM facts f
            JOIN facts_fts fts ON fts.rowid = f.fact_id
            WHERE {' AND '.join(where_clauses)}
              AND f.trust_score >= ?
            ORDER BY fts.rank
            LIMIT ?
        """

        try:
            rows = conn.execute(sql, params).fetchall()
        except Exception:
            rows = []

        # If FTS5 returned results, normalize rank and return
        if rows:
            results = [dict(r) for r in rows]
            ranks = [abs(r["fts_rank"]) for r in results]
            max_rank = max(ranks) if ranks else 1.0
            for r in results:
                r["fts_rank"] = 1.0 - (abs(r["fts_rank"]) / max_rank) if max_rank > 0 else 0.5
            return results

        # Stage 2: FTS5 failed (likely Chinese query) — fallback to LIKE
        return self._like_fallback(query, category, min_trust, limit)

    @staticmethod
    def _build_fts_query(query: str) -> str:
        """Build FTS5 query with prefix matching for better Chinese support.

        Each word gets a '*' suffix for prefix matching, which helps with
        Chinese terms that get merged by unicode61 tokenizer.
        """
        if not query:
            return ""

        words = query.strip().split()
        if not words:
            return ""

        fts_parts = []
        for word in words:
            if word:
                fts_parts.append(f"{word}*")

        if len(fts_parts) == 1:
            return fts_parts[0]
        else:
            return " OR ".join(fts_parts)

    def _like_fallback(
        self,
        query: str,
        category: str | None,
        min_trust: float,
        limit: int,
    ) -> list[dict]:
        """Fallback search using LIKE for Chinese/special character queries.

        Tokenizes query on Chinese-Latin boundaries and uses '%term%' LIKE.
        """
        conn = self.store._conn
        tokens = self._tokenize_for_like(query)

        if not tokens:
            return []

        params: list = []
        like_clauses = []
        for token in tokens:
            like_clauses.append("f.content LIKE ? OR f.tags LIKE ?")
            params.append(f"%{token}%")
            params.append(f"%{token}%")

        like_where = " OR ".join(like_clauses)
        category_clause = ""
        if category:
            category_clause = "AND f.category = ?"
            params.append(category)

        params.append(min_trust)
        params.append(limit)

        sql = f"""
            SELECT f.fact_id, f.content, f.category, f.tags,
                   f.trust_score, f.retrieval_count, f.helpful_count,
                   f.created_at, f.updated_at, f.hrr_vector,
                   0.5 as fts_rank  -- neutral rank for LIKE matches
            FROM facts f
            WHERE ({like_where})
              {category_clause}
              AND f.trust_score >= ?
            ORDER BY f.trust_score DESC
            LIMIT ?
        """

        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def _tokenize_for_like(text: str) -> list[str]:
        """Split text at Chinese-Latin boundaries for LIKE queries.

        'WSL网络关键事实' -> ['WSL', '网络', '关键', '事实']
        'MiMo性能问题' -> ['MiMo', '性能', '问题']
        """
        if not text:
            return []

        tokens = []
        current = ""
        for char in text:
            if '\u4e00' <= char <= '\u9fff' or '\u3000' <= char <= '\u303f':
                # Chinese/Japanese character
                if current and not all('\u4e00' <= c <= '\u9fff' for c in current):
                    tokens.append(current.strip())
                    current = ""
                current += char
            elif char.isalnum() or char in "-_.":
                current += char
            else:
                if current:
                    tokens.append(current.strip())
                    current = ""
        if current:
            tokens.append(current.strip())

        # Filter empty and short tokens
        return [t for t in tokens if len(t) >= 1]

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        """Tokenize text into a set of lowercase tokens."""
        if not text:
            return set()
        tokens = text.lower().split()
        return {t.strip(".,!?;:\"'()[]{}") for t in tokens if t.strip(".,!?;:\"'()[]{}")}

    @staticmethod
    def _jaccard_similarity(a: set[str], b: set[str]) -> float:
        """Jaccard similarity between two token sets."""
        if not a or not b:
            return 0.0
        intersection = a & b
        union = a | b
        return len(intersection) / len(union)

    def _temporal_decay(self, timestamp_str: str | None) -> float:
        """Compute temporal decay factor. Returns 1.0 if half_life is 0 or no timestamp."""
        if self.half_life <= 0 or not timestamp_str:
            return 1.0
        try:
            if "T" in timestamp_str:
                ts = datetime.fromisoformat(timestamp_str)
            else:
                ts = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            age_days = (datetime.now(timezone.utc) - ts.replace(tzinfo=timezone.utc)).days
            return 0.5 ** (age_days / self.half_life)
        except (ValueError, TypeError):
            return 1.0
