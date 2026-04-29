# /opt/voicegpt_sce/core/tenant_profile_resolver.py

from __future__ import annotations

from typing import Dict, Any

from core.db import db_one


class TenantProfileResolverError(Exception):
    pass


def resolve_tenant_profile_type(tenant_id: int) -> str:
    row = db_one(
        """
        SELECT profile_type
        FROM core.tenant_profiles
        WHERE tenant_id = %s
          AND is_active = true
        """,
        (tenant_id,),
    )

    if not row:
        raise TenantProfileResolverError(
            f"No active tenant profile binding for tenant_id={tenant_id}"
        )

    profile_type = (row.get("profile_type") or "").strip().upper()

    if profile_type not in {"FRONTDESK", "VIP"}:
        raise TenantProfileResolverError(
            f"Unsupported profile_type={profile_type} for tenant_id={tenant_id}"
        )

    return profile_type


def load_frontdesk_profile(tenant_id: int) -> Dict[str, Any]:
    row = db_one(
        """
        SELECT tenant_id, language, hours, address, phone, services,
               greeting, anything_else, clarify, farewell, escalation_target,
               keep_open, updated_at
        FROM core.frontdesk_profiles
        WHERE tenant_id = %s
        """,
        (tenant_id,),
    )

    if not row:
        raise TenantProfileResolverError(
            f"frontdesk profile not found for tenant_id={tenant_id}"
        )

    return row


def load_vip_profile(tenant_id: int) -> Dict[str, Any]:
    row = db_one(
        """
        SELECT tenant_id, language, persona, preferences,
               greeting, farewell, keep_open, updated_at
        FROM core.vip_profiles
        WHERE tenant_id = %s
        """,
        (tenant_id,),
    )

    if not row:
        raise TenantProfileResolverError(
            f"vip profile not found for tenant_id={tenant_id}"
        )

    return row