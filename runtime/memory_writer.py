import json
import re
from typing import Dict, Any, Optional, Tuple

from core.db import db_exec


def _extract_fact(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None

    t = text.strip()

    m = re.match(r"^\s*my name is\s+(.+?)\s*$", t, re.IGNORECASE)
    if m:
        value = m.group(1).strip().strip(".")
        if value:
            return {
                "memory_kind": "fact",
                "field": "name",
                "content": {"name": value},
            }

    m = re.match(r"^\s*call me\s+(.+?)\s*$", t, re.IGNORECASE)
    if m:
        value = m.group(1).strip().strip(".")
        if value:
            return {
                "memory_kind": "fact",
                "field": "name",
                "content": {"name": value},
            }

    m = re.match(r"^\s*my favorite color is\s+(.+?)\s*$", t, re.IGNORECASE)
    if m:
        value = m.group(1).strip().strip(".")
        if value:
            return {
                "memory_kind": "preference",
                "field": "favorite_color",
                "content": {"favorite_color": value},
            }

    m = re.match(r"^\s*my favourite color is\s+(.+?)\s*$", t, re.IGNORECASE)
    if m:
        value = m.group(1).strip().strip(".")
        if value:
            return {
                "memory_kind": "preference",
                "field": "favorite_color",
                "content": {"favorite_color": value},
            }

    m = re.match(r"^\s*my favorite food is\s+(.+?)\s*$", t, re.IGNORECASE)
    if m:
        value = m.group(1).strip().strip(".")
        if value:
            return {
                "memory_kind": "preference",
                "field": "favorite_food",
                "content": {"favorite_food": value},
            }

    m = re.match(r"^\s*my favourite food is\s+(.+?)\s*$", t, re.IGNORECASE)
    if m:
        value = m.group(1).strip().strip(".")
        if value:
            return {
                "memory_kind": "preference",
                "field": "favorite_food",
                "content": {"favorite_food": value},
            }

    return None


def _deactivate_previous_value(subject_id: str, field: str) -> None:
    if field == "name":
        db_exec(
            """
            UPDATE runtime.memory_items
            SET status = 'inactive'
            WHERE subject_type = 'user'
              AND subject_id = %s
              AND status = 'active'
              AND content ? 'name'
            """,
            (subject_id,),
        )
        return

    if field == "favorite_color":
        db_exec(
            """
            UPDATE runtime.memory_items
            SET status = 'inactive'
            WHERE subject_type = 'user'
              AND subject_id = %s
              AND status = 'active'
              AND content ? 'favorite_color'
            """,
            (subject_id,),
        )
        return

    if field == "favorite_food":
        db_exec(
            """
            UPDATE runtime.memory_items
            SET status = 'inactive'
            WHERE subject_type = 'user'
              AND subject_id = %s
              AND status = 'active'
              AND content ? 'favorite_food'
            """,
            (subject_id,),
        )
        return


def write_memory_if_detected(
    tenant_id: int,
    subject_id: str,
    text: str,
    source: str = "phase88d_runtime_write",
) -> Optional[Dict[str, Any]]:
    fact = _extract_fact(text)
    if not fact:
        return None

    memory_kind = fact["memory_kind"]
    field = fact["field"]
    content = fact["content"]

    _deactivate_previous_value(subject_id, field)

    db_exec(
        """
        INSERT INTO runtime.memory_items (
            memory_id,
            subject_type,
            subject_id,
            memory_kind,
            content,
            source,
            status,
            created_at
        )
        VALUES (
            gen_random_uuid(),
            'user',
            %s,
            %s,
            %s::jsonb,
            %s,
            'active',
            NOW()
        )
        """,
        (
            subject_id,
            memory_kind,
            json.dumps(content),
            source,
        ),
    )

    return fact