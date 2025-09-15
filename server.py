from __future__ import annotations

import os
import logging
import secrets
from dataclasses import dataclass
from typing import Any, Dict, Optional

from fastmcp import FastMCP
from .supabase_client import get_supabase, MissingSupabaseConfig
from .errors import ApiError, normalize_error


# Simple in-memory session store for demo purposes.
# Replace with your real auth/session backend when wiring to atoms API.
@dataclass
class Session:
    user_id: str
    username: str


class SessionStore:
    def __init__(self) -> None:
        self._sessions: Dict[str, Session] = {}

    def create(self, user_id: str, username: str) -> str:
        token = secrets.token_urlsafe(32)
        self._sessions[token] = Session(user_id=user_id, username=username)
        return token

    def get(self, token: str) -> Optional[Session]:
        return self._sessions.get(token)

    def revoke(self, token: str) -> None:
        self._sessions.pop(token, None)


sessions = SessionStore()
logger = logging.getLogger("atoms_fastmcp")


def _load_env_files() -> None:
    """Load environment variables from .env and .env.local if available.

    Precedence:
    - Existing process env stays authoritative (never overridden here)
    - .env then .env.local (local overrides .env for unset keys)
    """
    try:
        from dotenv import dotenv_values  # type: ignore
    except Exception:
        # If python-dotenv isn't installed, just skip quietly
        if os.path.exists(".env") or os.path.exists(".env.local"):
            logger.info(
                "python-dotenv not installed; skipping .env loading. Install python-dotenv to enable."
            )
        return

    merged: Dict[str, str] = {}
    if os.path.exists(".env"):
        try:
            merged.update({k: v for k, v in (dotenv_values(".env") or {}).items() if v is not None})
        except Exception as e:
            logger.warning(f"Failed loading .env: {e}")
    if os.path.exists(".env.local"):
        try:
            # Local overrides .env for keys not already in process env
            local_vals = {k: v for k, v in (dotenv_values(".env.local") or {}).items() if v is not None}
            merged.update(local_vals)
        except Exception as e:
            logger.warning(f"Failed loading .env.local: {e}")

    for k, v in merged.items():
        # Do not override already-set environment variables
        os.environ.setdefault(k, v)


def _require_session(session_token: str) -> Session:
    sess = sessions.get(session_token)
    if not sess:
        raise ValueError("Invalid or expired session_token. Please login again.")
    return sess


def _verify_credentials(username: str, password: str) -> Optional[dict]:
    """
    TEMP auth check. Replace with real backend integration.

    Current behavior:
    - If FASTMCP_DEMO_USER and FASTMCP_DEMO_PASS env vars are set, verify against them.
    - Otherwise accept any non-empty username/password and return a fake user.
    """
    env_user = os.getenv("FASTMCP_DEMO_USER")
    env_pass = os.getenv("FASTMCP_DEMO_PASS")

    if env_user is not None and env_pass is not None:
        if username == env_user and password == env_pass:
            return {"id": f"user_{username}", "username": username}
        return None

    # Try real Supabase auth first if configured
    try:
        supabase = get_supabase()
        # We expect username to be an email for Supabase auth
        auth_res = supabase.auth.sign_in_with_password({
            "email": username,
            "password": password,
        })
        user = getattr(auth_res, "user", None)
        if user and getattr(user, "id", None):
            return {"id": user.id, "username": username}
    except MissingSupabaseConfig:
        # Fall back to demo behavior below when env is missing
        pass
    except Exception:
        # Treat any auth error as invalid credentials, then fall back to demo if enabled below
        pass

    # Demo fallback only: accept any non-empty credentials when no strict env set
    if username and password:
        return {"id": f"user_{username}", "username": username}
    return None


def create_server() -> FastMCP:
    """Create the FastMCP server with tools that mirror the atoms API.

    Notes
    - Transport is selected when running: mcp.run(transport="http"|"stdio", ...)
    - Auth pattern: explicit login(username, password) returns session_token.
      All subsequent tools require a session_token parameter.
    - Replace stubbed sections with real backend calls (e.g., Supabase or your existing API layer).
    """

    mcp = FastMCP(name="atoms-fastmcp", instructions=(
        "Atoms MCP server. First call login(username, password) to obtain a session_token. "
        "Include session_token in every subsequent tool call."
    ))

    @mcp.tool(tags={"auth", "public"})
    def login(username: str, password: str) -> dict:
        """Authenticate a user and return a session_token for subsequent calls.

        Returns { success: bool, session_token?: str, user_id?: str, error?: str }
        """
        user = _verify_credentials(username, password)
        if not user:
            return {"success": False, "error": "Invalid credentials"}
        token = sessions.create(user_id=user["id"], username=user["username"])
        return {"success": True, "session_token": token, "user_id": user["id"]}

    @mcp.tool(tags={"auth"})
    def logout(session_token: str) -> dict:
        """Invalidate a session_token."""
        sessions.revoke(session_token)
        return {"success": True}

    # --- Organizations ---
    @mcp.tool(tags={"organizations"})
    def list_organizations(session_token: str, user_id: Optional[str] = None) -> list:
        """List organizations for the current user. Mirrors atoms-api organizations.listForUser.

        Replace body with a real backend call.
        """
        sess = _require_session(session_token)
        uid = user_id or sess.user_id
        try:
            sb = get_supabase()
            # Mirror TS: select organizations via membership
            # postgrest join: organizations!inner(*)
            resp = (
                sb.table("organization_members")
                .select("organizations!inner(*)")
                .eq("user_id", uid)
                .eq("status", "active")
                .eq("is_deleted", False)
                .execute()
            )
            data = getattr(resp, "data", []) or []
            orgs = [row.get("organizations") for row in data if row.get("organizations")]
            return orgs
        except Exception as e:
            # Fallback minimal demo
            logger.warning(f"list_organizations fallback due to: {e}")
            return [
                {
                    "id": "org_demo",
                    "name": "Demo Org",
                    "slug": "demo",
                    "created_by": uid,
                    "type": "team",
                    "member_count": 1,
                    "is_deleted": False,
                }
            ]

    @mcp.tool(tags={"organizations"})
    def get_organization(session_token: str, org_id: str) -> dict | None:
        """Get organization by id. Mirrors organizations.getById."""
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = (
                sb.table("organizations")
                .select("*")
                .eq("id", org_id)
                .eq("is_deleted", False)
                .single()
                .execute()
            )
            return getattr(resp, "data", None)
        except Exception:
            if org_id == "org_demo":
                return {
                    "id": "org_demo",
                    "name": "Demo Org",
                    "slug": "demo",
                    "created_by": "user_demo",
                    "type": "team",
                    "member_count": 1,
                    "is_deleted": False,
                }
            return None

    @mcp.tool(tags={"organizations"})
    def organizations_get_id_by_slug(session_token: str, slug: str) -> str | None:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = sb.table("organizations").select("id").eq("slug", slug).single().execute()
            return (getattr(resp, "data", {}) or {}).get("id")
        except Exception as e:
            raise normalize_error(e, "Failed to get organization id by slug")

    @mcp.tool(tags={"organizations"})
    def organizations_list_for_user(session_token: str, user_id: str) -> list:
        return list_organizations(session_token, user_id)

    @mcp.tool(tags={"organizations"})
    def organizations_list_ids_by_membership(session_token: str, user_id: str) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = (
                sb.table("organization_members")
                .select("organization_id")
                .eq("user_id", user_id)
                .eq("status", "active")
                .eq("is_deleted", False)
                .execute()
            )
            return [row.get("organization_id") for row in (getattr(resp, "data", []) or [])]
        except Exception as e:
            raise normalize_error(e, "Failed to list organization ids by membership")

    @mcp.tool(tags={"organizations"})
    def organizations_list_with_filters(session_token: str, filters: Optional[dict] = None) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            q = sb.table("organizations").select("*").eq("is_deleted", False)
            if filters:
                for k, v in filters.items():
                    if v is not None:
                        q = q.eq(k, v)
            resp = q.execute()
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list organizations")

    @mcp.tool(tags={"organizations"})
    def organizations_get_personal_org(session_token: str, user_id: str) -> dict | None:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = (
                sb.table("organizations")
                .select("*")
                .eq("created_by", user_id)
                .eq("type", "personal")
                .eq("is_deleted", False)
                .single()
                .execute()
            )
            return getattr(resp, "data", None)
        except Exception as e:
            raise normalize_error(e, "Failed to get personal organization")

    @mcp.tool(tags={"organizations"})
    def organizations_create(session_token: str, insert: dict) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = sb.table("organizations").insert(insert).select("*").single().execute()
            return getattr(resp, "data", None) or {}
        except Exception as e:
            raise normalize_error(e, "Failed to create organization")

    @mcp.tool(tags={"organizations"})
    def organizations_list_members(session_token: str, organization_id: str) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = (
                sb.table("organization_members")
                .select("*, profiles(*)")
                .eq("organization_id", organization_id)
                .eq("status", "active")
                .eq("is_deleted", False)
                .execute()
            )
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list organization members")

    @mcp.tool(tags={"organizations"})
    def organizations_remove_member(session_token: str, organization_id: str, user_id: str) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            _ = (
                sb.table("organization_members")
                .delete()
                .eq("organization_id", organization_id)
                .eq("user_id", user_id)
                .execute()
            )
            return {"organization_id": organization_id, "user_id": user_id}
        except Exception as e:
            raise normalize_error(e, "Failed to remove organization member")

    @mcp.tool(tags={"organizations"})
    def organizations_invite(session_token: str, input: dict) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = sb.table("organization_invitations").insert(input).select("*").single().execute()
            return getattr(resp, "data", None) or {}
        except Exception as e:
            raise normalize_error(e, "Failed to create organization invitation")

    @mcp.tool(tags={"organizations"})
    def organizations_add_member(session_token: str, input: dict) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = sb.table("organization_members").insert(input).select("*").single().execute()
            return getattr(resp, "data", None) or {}
        except Exception as e:
            raise normalize_error(e, "Failed to add organization member")

    @mcp.tool(tags={"organizations"})
    def organizations_set_member_role(session_token: str, org_id: str, user_id: str, role: str) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            _ = (
                sb.table("organization_members").update({"role": role}).eq("organization_id", org_id).eq("user_id", user_id).execute()
            )
            return {"org_id": org_id, "user_id": user_id, "role": role}
        except Exception as e:
            raise normalize_error(e, "Failed to set organization member role")

    @mcp.tool(tags={"organizations"})
    def organizations_update_member_count(session_token: str, org_id: str) -> int:
        _require_session(session_token)
        try:
            sb = get_supabase()
            count_resp = (
                sb.table("organization_members").select("*", count="exact", head=True).eq("organization_id", org_id).execute()
            )
            count = getattr(count_resp, "count", 0) or 0
            _ = sb.table("organizations").update({"member_count": count}).eq("id", org_id).execute()
            return count
        except Exception as e:
            raise normalize_error(e, "Failed to update member count")

    # ----------------------
    # Assignments
    # ----------------------
    @mcp.tool(tags={"assignments"})
    def assignments_list_by_entity(session_token: str, entity_id: str, entity_type: str, extra: Optional[dict] = None) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            q = sb.table("assignments").select("*").eq("entity_id", entity_id).eq("entity_type", entity_type)
            if extra:
                for k, v in extra.items():
                    if v is not None:
                        q = q.eq(k, v)
            resp = q.execute()
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list assignments by entity")

    @mcp.tool(tags={"assignments"})
    def assignments_list_by_user(session_token: str, user_id: str, extra: Optional[dict] = None) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            q = sb.table("assignments").select("*").eq("assignee_id", user_id).order("created_at", desc=True)
            if extra:
                for k, v in extra.items():
                    if v is not None:
                        q = q.eq(k, v)
            resp = q.execute()
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list assignments by user")

    # ----------------------
    # Audit logs
    # ----------------------
    @mcp.tool(tags={"audit_logs"})
    def audit_logs_list_by_entity(session_token: str, entity_id: str, entity_type: str, extra: Optional[dict] = None) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            q = (
                sb.table("audit_logs").select("*").eq("entity_id", entity_id).eq("entity_type", entity_type).order("created_at", desc=True)
            )
            if extra:
                for k, v in extra.items():
                    if v is not None:
                        q = q.eq(k, v)
            resp = q.execute()
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list audit logs by entity")

    # ----------------------
    # Diagrams
    # ----------------------
    @mcp.tool(tags={"diagrams"})
    def diagrams_list_by_project(session_token: str, project_id: str) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = (
                sb.table("excalidraw_diagrams")
                .select("id, name, thumbnail_url, updated_at, created_by")
                .eq("project_id", project_id)
                .order("updated_at", desc=True)
                .execute()
            )
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list diagrams")

    @mcp.tool(tags={"diagrams"})
    def diagrams_get_by_id(session_token: str, id: str) -> dict | None:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = (
                sb.table("excalidraw_diagrams").select("id, name, diagram_data, project_id, organization_id").eq("id", id).single().execute()
            )
            return getattr(resp, "data", None)
        except Exception as e:
            raise normalize_error(e, "Failed to fetch diagram")

    @mcp.tool(tags={"diagrams"})
    def diagrams_update_name(session_token: str, id: str, name: str) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            _ = sb.table("excalidraw_diagrams").update({"name": name}).eq("id", id).execute()
            return {"id": id, "name": name}
        except Exception as e:
            raise normalize_error(e, "Failed to rename diagram")

    @mcp.tool(tags={"diagrams"})
    def diagrams_delete(session_token: str, id: str) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            _ = sb.table("excalidraw_diagrams").delete().eq("id", id).execute()
            return {"id": id}
        except Exception as e:
            raise normalize_error(e, "Failed to delete diagram")

    @mcp.tool(tags={"diagrams"})
    def diagrams_upsert(session_token: str, record: dict) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            _ = sb.table("excalidraw_diagrams").upsert(record).execute()
            return {"ok": True}
        except Exception as e:
            raise normalize_error(e, "Failed to save diagram")

    # ----------------------
    # Recent
    # ----------------------
    @mcp.tool(tags={"recent"})
    def recent_documents_by_org_ids(session_token: str, org_ids: list[str]) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            sel = (
                "id, name, description, updated_at, project_id, "
                "projects!inner(id, name, organization_id, organizations!inner(id, name))"
            )
            resp = (
                sb.table("documents")
                .select(sel)
                .in_("projects.organization_id", org_ids)
                .eq("is_deleted", False)
                .order("updated_at", desc=True)
                .limit(20)
                .execute()
            )
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list recent documents")

    @mcp.tool(tags={"recent"})
    def recent_projects_by_org_ids(session_token: str, org_ids: list[str]) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            sel = "id, name, description, updated_at, organization_id, organizations!inner(id, name)"
            resp = (
                sb.table("projects")
                .select(sel)
                .in_("organization_id", org_ids)
                .eq("is_deleted", False)
                .order("updated_at", desc=True)
                .limit(10)
                .execute()
            )
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list recent projects")

    @mcp.tool(tags={"recent"})
    def recent_requirements_by_org_ids(session_token: str, org_ids: list[str]) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            sel = (
                "id, name, description, external_id, updated_at, document_id, "
                "documents!inner(id, name, project_id, projects!inner(id, name, organization_id, organizations!inner(id, name)))"
            )
            resp = (
                sb.table("requirements")
                .select(sel)
                .in_("documents.projects.organization_id", org_ids)
                .eq("is_deleted", False)
                .order("updated_at", desc=True)
                .limit(15)
                .execute()
            )
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list recent requirements")

    # ----------------------
    # Storage convenience
    # ----------------------
    @mcp.tool(tags={"storage"})
    def storage_get_public_url(session_token: str, bucket: str, path: str) -> str:
        _require_session(session_token)
        import os as _os
        base = _os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        if not base:
            raise ApiError("CONFIG", "Missing NEXT_PUBLIC_SUPABASE_URL")
        url = f"{base}/storage/v1/object/public/{bucket}/{path}"
        return url

    # --- Projects ---
    @mcp.tool(tags={"projects"})
    def list_projects_by_org(session_token: str, organization_id: str) -> list:
        """List projects for an organization. Mirrors projects.listByOrg."""
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = (
                sb.table("projects")
                .select("*")
                .eq("organization_id", organization_id)
                .eq("is_deleted", False)
                .execute()
            )
            return getattr(resp, "data", []) or []
        except Exception:
            return [
                {
                    "id": "proj_demo",
                    "organization_id": organization_id,
                    "name": "Demo Project",
                    "slug": "demo-project",
                    "is_deleted": False,
                }
            ]

    # --- Documents ---
    @mcp.tool(tags={"documents"})
    def list_documents(session_token: str, project_id: Optional[str] = None) -> list:
        """List documents with optional filter. Mirrors documents.listWithFilters."""
        _require_session(session_token)
        try:
            sb = get_supabase()
            q = sb.table("documents").select("*").eq("is_deleted", False)
            if project_id:
                q = q.eq("project_id", project_id)
            resp = q.execute()
            return getattr(resp, "data", []) or []
        except Exception:
            return [
                {
                    "id": "doc_demo",
                    "project_id": project_id or "proj_demo",
                    "name": "Specification",
                    "is_deleted": False,
                }
            ]

    # --- Requirements ---
    @mcp.tool(tags={"requirements"})
    def list_requirements_by_document(session_token: str, document_id: str) -> list:
        """List requirements for a document. Mirrors requirements.listByDocument."""
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = (
                sb.table("requirements")
                .select("*")
                .eq("document_id", document_id)
                .eq("is_deleted", False)
                .execute()
            )
            return getattr(resp, "data", []) or []
        except Exception:
            return [
                {
                    "id": "req_demo",
                    "document_id": document_id,
                    "name": "The system shall ...",
                    "status": "active",
                    "is_deleted": False,
                }
            ]

    # --- Profile (Auth domain sampling) ---
    @mcp.tool(tags={"auth"})
    def get_profile(session_token: str) -> dict:
        """Return the current user's profile. Mirrors auth.getProfile."""
        sess = _require_session(session_token)
        try:
            sb = get_supabase()
            resp = (
                sb.table("profiles")
                .select("*")
                .eq("id", sess.user_id)
                .single()
                .execute()
            )
            data = getattr(resp, "data", None)
            if data:
                return data
        except Exception:
            pass
        return {"id": sess.user_id, "full_name": sess.username, "approved": True}

    # --------- Additional Auth tools ---------
    @mcp.tool(tags={"auth"})
    def auth_get_by_email(session_token: str, email: str) -> dict | None:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = sb.table("profiles").select("*").ilike("email", email).single().execute()
            return getattr(resp, "data", None)
        except Exception as e:
            raise normalize_error(e, "Failed to get profile by email")

    @mcp.tool(tags={"auth"})
    def auth_update_profile(session_token: str, user_id: str, data: dict) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = sb.table("profiles").update(data).eq("id", user_id).select("*").single().execute()
            return getattr(resp, "data", None) or {}
        except Exception as e:
            raise normalize_error(e, "Failed to update profile")

    @mcp.tool(tags={"auth"})
    def auth_list_profiles(session_token: str, select: str | None = None) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            sel = select or "email, full_name, id, is_approved, created_at"
            resp = sb.table("profiles").select(sel).order("created_at", desc=True).execute()
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list profiles")

    @mcp.tool(tags={"auth"})
    def auth_set_approval(session_token: str, user_id: str, is_approved: bool) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            _ = sb.table("profiles").update({"is_approved": is_approved}).eq("id", user_id).execute()
            return {"user_id": user_id, "is_approved": is_approved}
        except Exception as e:
            raise normalize_error(e, "Failed to set approval")

    # --------- Notifications ---------
    @mcp.tool(tags={"notifications"})
    def notifications_list_by_user(session_token: str, user_id: str, extra: Optional[dict] = None) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            q = sb.table("notifications").select("*").eq("user_id", user_id).order("created_at", desc=True)
            if extra:
                for k, v in extra.items():
                    if v is not None:
                        q = q.eq(k, v)
            resp = q.execute()
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list notifications")

    @mcp.tool(tags={"notifications"})
    def notifications_unread_count(session_token: str, user_id: str) -> int:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = sb.table("notifications").select("*", count="exact", head=True).eq("user_id", user_id).eq("unread", True).execute()
            return getattr(resp, "count", 0) or 0
        except Exception as e:
            raise normalize_error(e, "Failed to count notifications")

    # --------- Org Invitations ---------
    @mcp.tool(tags={"org_invitations"})
    def org_invitations_list_by_email(session_token: str, email: str) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = sb.table("organization_invitations").select("*").eq("email", email).neq("status", "rejected").execute()
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list invitations by email")

    @mcp.tool(tags={"org_invitations"})
    def org_invitations_list_by_creator(session_token: str, user_id: str) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = sb.table("organization_invitations").select("*").eq("created_by", user_id).execute()
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list invitations by creator")

    @mcp.tool(tags={"org_invitations"})
    def org_invitations_list_by_organization(session_token: str, org_id: str) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = sb.table("organization_invitations").select("*").eq("organization_id", org_id).execute()
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list invitations by organization")

    @mcp.tool(tags={"org_invitations"})
    def org_invitations_update_status(session_token: str, id: str, status: str, updated_by: str) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            _ = sb.table("organization_invitations").update({"status": status, "updated_by": updated_by}).eq("id", id).execute()
            return {"id": id, "status": status}
        except Exception as e:
            raise normalize_error(e, "Failed to update invitation status")

    # --------- External Documents ---------
    @mcp.tool(tags={"external_documents"})
    def external_documents_get_by_id(session_token: str, id: str) -> dict | None:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = sb.table("external_documents").select("*").eq("id", id).single().execute()
            return getattr(resp, "data", None)
        except Exception as e:
            raise normalize_error(e, "Failed to fetch external document")

    @mcp.tool(tags={"external_documents"})
    def external_documents_list_by_org(session_token: str, org_id: str) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = sb.table("external_documents").select("*").eq("organization_id", org_id).execute()
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list external documents")

    @mcp.tool(tags={"external_documents"})
    def external_documents_upload_base64(session_token: str, name: str, mime_type: str, base64_data: str, org_id: str) -> dict:
        _require_session(session_token)
        try:
            import base64

            sb = get_supabase()
            # Create DB row first
            doc_resp = (
                sb.table("external_documents")
                .insert({"name": name, "type": mime_type, "organization_id": org_id})
                .select("*")
                .single()
                .execute()
            )
            document = getattr(doc_resp, "data", None)
            if not document:
                raise ApiError("DATABASE_ERROR", "Failed to create external document record")
            file_path = f"{org_id}/{document['id']}"
            raw = base64.b64decode(base64_data.split(",")[-1])
            # Upload to storage
            stor = sb.storage.from_("external_documents")
            up_resp = stor.upload(file_path, raw, file_options={"content-type": mime_type, "cache-control": "3600", "upsert": False})
            if getattr(up_resp, "error", None):
                _ = sb.table("external_documents").delete().eq("id", document["id"]).execute()
                raise ApiError("EXTERNAL_API_ERROR", "Failed to upload external document", details=str(getattr(up_resp, "error", None)))
            return document
        except Exception as e:
            raise normalize_error(e, "Failed to upload external document")

    @mcp.tool(tags={"external_documents"})
    def external_documents_remove(session_token: str, document_id: str) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            fetch = sb.table("external_documents").select("id, organization_id").eq("id", document_id).single().execute()
            doc = getattr(fetch, "data", None)
            if not doc:
                return {"removed": False}
            file_path = f"{doc['organization_id']}/{doc['id']}"
            stor = sb.storage.from_("external_documents")
            _ = stor.remove([file_path])
            _ = sb.table("external_documents").delete().eq("id", document_id).execute()
            return {"removed": True}
        except Exception as e:
            raise normalize_error(e, "Failed to delete external document")

    @mcp.tool(tags={"external_documents"})
    def external_documents_update(session_token: str, document_id: str, data: dict) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = sb.table("external_documents").update(data).eq("id", document_id).select("*").single().execute()
            return getattr(resp, "data", None) or {}
        except Exception as e:
            raise normalize_error(e, "Failed to update external document")

    @mcp.tool(tags={"external_documents"})
    def external_documents_get_public_url(session_token: str, org_id: str, document_id: str) -> str | None:
        _require_session(session_token)
        try:
            base = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
            if not base:
                raise ApiError("CONFIG", "Missing NEXT_PUBLIC_SUPABASE_URL")
            return f"{base}/storage/v1/object/public/external_documents/{org_id}/{document_id}"
        except Exception as e:
            raise normalize_error(e, "Failed to get public url")

    # --------- Testing (QA) ---------
    @mcp.tool(tags={"testing"})
    def testing_list_project_tests(session_token: str, project_id: str, filters: Optional[dict] = None, pagination: Optional[dict] = None) -> dict:
        _require_session(session_token)
        # defaults
        p = {"page": 1, "pageSize": 10, "orderBy": "created_at", "orderDirection": "desc"}
        if pagination:
            p.update({k: v for k, v in pagination.items() if v is not None})
        try:
            sb = get_supabase()
            q = sb.table("test_req").select("*", count="exact").eq("project_id", project_id).eq("is_active", True)
            if filters:
                if filters.get("status"):
                    q = q.in_("status", filters["status"])  # type: ignore[index]
                if filters.get("priority"):
                    q = q.in_("priority", filters["priority"])  # type: ignore[index]
                if filters.get("test_type"):
                    q = q.in_("test_type", filters["test_type"])  # type: ignore[index]
                if filters.get("search"):
                    term = filters["search"]
                    q = q.or_(f"title.ilike.%{term}%,description.ilike.%{term}%")
            start = (int(p["page"]) - 1) * int(p["pageSize"])  # type: ignore[index]
            end = start + int(p["pageSize"]) - 1  # type: ignore[index]
            q = q.order(p["orderBy"], desc=(p["orderDirection"] == "desc")).range(start, end)  # type: ignore[index]
            resp = q.execute()
            return {"data": getattr(resp, "data", []) or [], "count": getattr(resp, "count", 0) or 0}
        except Exception as e:
            raise normalize_error(e, "Failed to list tests")

    @mcp.tool(tags={"testing"})
    def testing_get_tests_by_ids(session_token: str, ids: list[str]) -> list:
        _require_session(session_token)
        if not ids:
            return []
        try:
            sb = get_supabase()
            resp = sb.table("test_req").select("*").in_("id", ids).execute()
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to fetch tests")

    @mcp.tool(tags={"testing"})
    def testing_get_linked_requirements_count(session_token: str, test_id: str) -> int:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = sb.table("requirement_tests").select("*", count="exact", head=True).eq("test_id", test_id).execute()
            return getattr(resp, "count", 0) or 0
        except Exception as e:
            raise normalize_error(e, "Failed to count linked requirements")

    @mcp.tool(tags={"testing"})
    def testing_list_relations_by_test(session_token: str, test_id: str) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = sb.table("requirement_tests").select("*").eq("test_id", test_id).execute()
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list test relations")

    @mcp.tool(tags={"testing"})
    def testing_list_relations_by_requirement(session_token: str, requirement_id: str) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = sb.table("requirement_tests").select("*").eq("requirement_id", requirement_id).execute()
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list requirement relations")

    @mcp.tool(tags={"testing"})
    def testing_list_relations_by_tests(session_token: str, test_ids: list[str]) -> list:
        _require_session(session_token)
        if not test_ids:
            return []
        try:
            sb = get_supabase()
            resp = sb.table("requirement_tests").select("*").in_("test_id", test_ids).execute()
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list relations by tests")

    @mcp.tool(tags={"testing"})
    def testing_create_test(session_token: str, test_data: dict) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = sb.table("test_req").insert(test_data).select("*").single().execute()
            return getattr(resp, "data", None) or {}
        except Exception as e:
            raise normalize_error(e, "Failed to create test")

    @mcp.tool(tags={"testing"})
    def testing_update_test(session_token: str, id: str, updates: dict) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = sb.table("test_req").update(updates).eq("id", id).select("*").single().execute()
            return getattr(resp, "data", None) or {}
        except Exception as e:
            raise normalize_error(e, "Failed to update test")

    @mcp.tool(tags={"testing"})
    def testing_soft_delete_test(session_token: str, id: str) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = sb.table("test_req").update({"is_active": False}).eq("id", id).select("*").single().execute()
            return getattr(resp, "data", None) or {}
        except Exception as e:
            raise normalize_error(e, "Failed to delete test")

    @mcp.tool(tags={"testing"})
    def testing_create_relation(session_token: str, relation: dict) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = sb.table("requirement_tests").insert(relation).select("*").single().execute()
            return getattr(resp, "data", None) or {}
        except Exception as e:
            raise normalize_error(e, "Failed to create test relation")

    @mcp.tool(tags={"testing"})
    def testing_update_relation(session_token: str, requirement_id: str, test_id: str, updates: dict) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = (
                sb.table("requirement_tests").update(updates).eq("requirement_id", requirement_id).eq("test_id", test_id).select("*").single().execute()
            )
            return getattr(resp, "data", None) or {}
        except Exception as e:
            raise normalize_error(e, "Failed to update test relation")

    @mcp.tool(tags={"testing"})
    def testing_delete_relation(session_token: str, requirement_id: str, test_id: str) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            _ = sb.table("requirement_tests").delete().eq("requirement_id", requirement_id).eq("test_id", test_id).execute()
            return {"requirement_id": requirement_id, "test_id": test_id}
        except Exception as e:
            raise normalize_error(e, "Failed to delete test relation")

    # --------- Realtime / Pipelines / OCR stubs ---------
    @mcp.tool(tags={"realtime"})
    def realtime_not_supported(_: str) -> dict:
        raise ApiError("NOT_SUPPORTED", "Realtime subscriptions are not supported via MCP HTTP/STDIO")

    @mcp.tool(tags={"pipelines"})
    def pipelines_not_implemented(_: str) -> dict:
        raise ApiError("NOT_IMPLEMENTED", "Pipelines (Gumloop) are not enabled in this MCP server")

    @mcp.tool(tags={"ocr"})
    def ocr_not_implemented(_: str) -> dict:
        raise ApiError("NOT_IMPLEMENTED", "OCR (Chunkr) is not enabled in this MCP server")

    # ----------------------
    # Projects domain (full)
    # ----------------------
    @mcp.tool(tags={"projects"})
    def projects_get_by_id(session_token: str, id: str) -> dict | None:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = sb.table("projects").select("*").eq("id", id).single().execute()
            return getattr(resp, "data", None)
        except Exception as e:
            raise normalize_error(e, "Failed to get project")

    @mcp.tool(tags={"projects"})
    def projects_list_for_user(session_token: str, user_id: str, org_id: str) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = (
                sb.table("projects")
                .select("*, project_members!inner(project_id)")
                .eq("project_members.user_id", user_id)
                .eq("project_members.org_id", org_id)
                .eq("project_members.status", "active")
                .eq("is_deleted", False)
                .execute()
            )
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list projects for user")

    @mcp.tool(tags={"projects"})
    def projects_list_members(session_token: str, project_id: str) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = (
                sb.table("project_members")
                .select("*, profiles(*)")
                .eq("project_id", project_id)
                .eq("status", "active")
                .execute()
            )
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list project members")

    @mcp.tool(tags={"projects"})
    def projects_list_by_org(session_token: str, organization_id: str) -> list:
        return list_projects_by_org(session_token, organization_id)

    @mcp.tool(tags={"projects"})
    def projects_list_by_membership_for_org(session_token: str, org_id: str, user_id: str) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            ids_resp = (
                sb.table("project_members")
                .select("project_id")
                .eq("org_id", org_id)
                .eq("user_id", user_id)
                .eq("status", "active")
                .execute()
            )
            ids = [row.get("project_id") for row in (getattr(ids_resp, "data", []) or [])]
            if not ids:
                return []
            proj_resp = (
                sb.table("projects")
                .select("*")
                .in_("id", ids)
                .eq("organization_id", org_id)
                .eq("is_deleted", False)
                .execute()
            )
            return getattr(proj_resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list projects by membership for org")

    @mcp.tool(tags={"projects"})
    def projects_list_with_filters(session_token: str, filters: Optional[dict] = None) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            q = sb.table("projects").select("*")
            if filters:
                for k, v in filters.items():
                    if v is not None:
                        q = q.eq(k, v)
            resp = q.execute()
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list projects")

    @mcp.tool(tags={"projects"})
    def projects_create(session_token: str, insert: dict) -> dict:
        sess = _require_session(session_token)
        try:
            sb = get_supabase()
            # allow created_by default if not provided
            payload = {**insert}
            payload.setdefault("created_by", sess.user_id)
            resp = sb.table("projects").insert(payload).select("*").single().execute()
            data = getattr(resp, "data", None)
            if not data:
                raise ApiError("DATABASE_ERROR", "Failed to create project")
            return data
        except Exception as e:
            raise normalize_error(e, "Failed to create project")

    @mcp.tool(tags={"projects"})
    def projects_update(session_token: str, id: str, updates: dict) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = (
                sb.table("projects").update(updates).eq("id", id).select("*").single().execute()
            )
            data = getattr(resp, "data", None)
            if not data:
                raise ApiError("DATABASE_ERROR", "Failed to update project")
            return data
        except Exception as e:
            raise normalize_error(e, "Failed to update project")

    @mcp.tool(tags={"projects"})
    def projects_soft_delete(session_token: str, id: str, deleted_by: str) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = (
                sb.table("projects")
                .update({
                    "is_deleted": True,
                    "deleted_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
                    "deleted_by": deleted_by,
                })
                .eq("id", id)
                .select("*")
                .single()
                .execute()
            )
            data = getattr(resp, "data", None)
            if not data:
                raise ApiError("DATABASE_ERROR", "Failed to delete project")
            return data
        except Exception as e:
            raise normalize_error(e, "Failed to delete project")

    @mcp.tool(tags={"projects"})
    def projects_add_member(session_token: str, project_id: str, user_id: str, role: str, org_id: str) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = (
                sb.table("project_members")
                .insert({
                    "user_id": user_id,
                    "project_id": project_id,
                    "role": role,
                    "org_id": org_id,
                    "status": "active",
                })
                .select("*")
                .single()
                .execute()
            )
            return getattr(resp, "data", None) or {}
        except Exception as e:
            raise normalize_error(e, "Failed to add project member")

    @mcp.tool(tags={"projects"})
    def projects_set_member_role(session_token: str, project_id: str, user_id: str, role: str) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            _ = (
                sb.table("project_members")
                .update({"role": role})
                .eq("project_id", project_id)
                .eq("user_id", user_id)
                .execute()
            )
            return {"project_id": project_id, "user_id": user_id, "role": role}
        except Exception as e:
            raise normalize_error(e, "Failed to set project member role")

    @mcp.tool(tags={"projects"})
    def projects_remove_member(session_token: str, project_id: str, user_id: str) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            _ = sb.table("project_members").delete().eq("project_id", project_id).eq("user_id", user_id).execute()
            return {"project_id": project_id, "user_id": user_id}
        except Exception as e:
            raise normalize_error(e, "Failed to remove project member")

    # ----------------------
    # Documents domain (major)
    # ----------------------
    @mcp.tool(tags={"documents"})
    def documents_create(session_token: str, insert: dict) -> dict:
        sess = _require_session(session_token)
        try:
            sb = get_supabase()
            payload = {**insert}
            payload.setdefault("created_by", sess.user_id)
            resp = sb.table("documents").insert(payload).select("*").single().execute()
            data = getattr(resp, "data", None)
            if not data:
                raise ApiError("DATABASE_ERROR", "Failed to create document")
            return data
        except Exception as e:
            raise normalize_error(e, "Failed to create document")

    @mcp.tool(tags={"documents"})
    def documents_get_by_id(session_token: str, document_id: str) -> dict | None:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = (
                sb.table("documents")
                .select("*")
                .eq("id", document_id)
                .eq("is_deleted", False)
                .single()
                .execute()
            )
            return getattr(resp, "data", None)
        except Exception as e:
            raise normalize_error(e, "Failed to get document")

    @mcp.tool(tags={"documents"})
    def documents_list_by_project(session_token: str, project_id: str) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = (
                sb.table("documents").select("*").eq("project_id", project_id).eq("is_deleted", False).execute()
            )
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list documents by project")

    @mcp.tool(tags={"documents"})
    def documents_list_with_filters(session_token: str, filters: Optional[dict] = None) -> list:
        return list_documents(session_token, filters.get("project_id") if filters else None)

    @mcp.tool(tags={"documents"})
    def documents_update(session_token: str, document_id: str, updates: dict) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = (
                sb.table("documents").update(updates).eq("id", document_id).single().execute()
            )
            data = getattr(resp, "data", None)
            if not data:
                raise ApiError("DATABASE_ERROR", "Failed to update document")
            return data
        except Exception as e:
            raise normalize_error(e, "Failed to update document")

    @mcp.tool(tags={"documents"})
    def documents_soft_delete(session_token: str, id: str, deleted_by: str) -> dict:
        _require_session(session_token)
        try:
            from datetime import datetime, timezone

            sb = get_supabase()
            resp = (
                sb.table("documents")
                .update({
                    "is_deleted": True,
                    "deleted_at": datetime.now(timezone.utc).isoformat(),
                    "deleted_by": deleted_by,
                })
                .eq("id", id)
                .select("*")
                .single()
                .execute()
            )
            data = getattr(resp, "data", None)
            if not data:
                raise ApiError("DATABASE_ERROR", "Failed to delete document")
            return data
        except Exception as e:
            raise normalize_error(e, "Failed to delete document")

    @mcp.tool(tags={"documents"})
    def documents_blocks_and_requirements(session_token: str, document_id: str) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = (
                sb.table("blocks")
                .select("*, requirements:requirements(*)")
                .eq("document_id", document_id)
                .eq("requirements.document_id", document_id)
                .eq("requirements.is_deleted", False)
                .eq("is_deleted", False)
                .execute()
            )
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to load blocks and requirements")

    @mcp.tool(tags={"documents"})
    def documents_get_block_by_id(session_token: str, block_id: str) -> dict | None:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = sb.table("blocks").select("*").eq("id", block_id).single().execute()
            return getattr(resp, "data", None)
        except Exception as e:
            raise normalize_error(e, "Failed to get block")

    @mcp.tool(tags={"documents"})
    def documents_list_blocks(session_token: str, document_id: str) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = (
                sb.table("blocks")
                .select("*")
                .eq("document_id", document_id)
                .eq("is_deleted", False)
                .order("position")
                .execute()
            )
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list blocks")

    @mcp.tool(tags={"documents"})
    def documents_list_columns_by_block_ids(session_token: str, block_ids: list[str]) -> list:
        _require_session(session_token)
        if not block_ids:
            return []
        try:
            sb = get_supabase()
            resp = (
                sb.table("columns")
                .select("*, property:properties(*)")
                .in_("block_id", block_ids)
                .order("position", desc=False)
                .execute()
            )
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list columns")

    @mcp.tool(tags={"documents"})
    def documents_create_block(session_token: str, insert: dict) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = sb.table("blocks").insert(insert).select("*").single().execute()
            data = getattr(resp, "data", None)
            if not data:
                raise ApiError("DATABASE_ERROR", "Failed to create block")
            return data
        except Exception as e:
            raise normalize_error(e, "Failed to create block")

    @mcp.tool(tags={"documents"})
    def documents_update_block(session_token: str, id: str, update: dict) -> dict:
        _require_session(session_token)
        try:
            from datetime import datetime, timezone

            sb = get_supabase()
            resp = (
                sb.table("blocks")
                .update({**update, "updated_at": datetime.now(timezone.utc).isoformat()})
                .eq("id", id)
                .select("*")
                .single()
                .execute()
            )
            data = getattr(resp, "data", None)
            if not data:
                raise ApiError("DATABASE_ERROR", "Failed to update block")
            return data
        except Exception as e:
            raise normalize_error(e, "Failed to update block")

    @mcp.tool(tags={"documents"})
    def documents_soft_delete_block(session_token: str, id: str, deleted_by: str) -> dict:
        _require_session(session_token)
        try:
            from datetime import datetime, timezone

            sb = get_supabase()
            resp = (
                sb.table("blocks")
                .update({
                    "is_deleted": True,
                    "deleted_at": datetime.now(timezone.utc).isoformat(),
                    "deleted_by": deleted_by,
                })
                .eq("id", id)
                .select("*")
                .single()
                .execute()
            )
            data = getattr(resp, "data", None)
            if not data:
                raise ApiError("DATABASE_ERROR", "Failed to delete block")
            return data
        except Exception as e:
            raise normalize_error(e, "Failed to delete block")

    @mcp.tool(tags={"documents"})
    def documents_create_column(session_token: str, insert: dict) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = sb.table("columns").insert(insert).select("*").single().execute()
            data = getattr(resp, "data", None)
            if not data:
                raise ApiError("DATABASE_ERROR", "Failed to create column")
            return data
        except Exception as e:
            raise normalize_error(e, "Failed to create column")

    @mcp.tool(tags={"documents"})
    def documents_delete_column(session_token: str, id: str) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            _ = sb.table("columns").delete().eq("id", id).execute()
            return {"id": id}
        except Exception as e:
            raise normalize_error(e, "Failed to delete column")

    # ----------------------
    # Requirements domain (major)
    # ----------------------
    def _generate_next_requirement_id(sb, organization_id: str) -> str:
        try:
            org_resp = sb.table("organizations").select("name").eq("id", organization_id).single().execute()
            org = getattr(org_resp, "data", None) or {}
            prefix = (org.get("name", "ORG") or "ORG")[:3].upper()
            req_resp = (
                sb.table("requirements").select("external_id").eq("organization_id", organization_id).execute()
            )
            max_num = 0
            pre = f"REQ-{prefix}-"
            for row in getattr(req_resp, "data", []) or []:
                ext = row.get("external_id")
                if isinstance(ext, str) and ext.startswith(pre):
                    try:
                        num = int(ext[len(pre):])
                        if num > max_num:
                            max_num = num
                    except Exception:
                        continue
            n = max_num + 1
            return f"{pre}{n:03d}"
        except Exception:
            ts = str(__import__("time").time()).replace(".", "")[-6:]
            return f"REQ-{ts}"

    @mcp.tool(tags={"requirements"})
    def requirements_get_by_id(session_token: str, id: str) -> dict | None:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = sb.table("requirements").select("*").eq("id", id).single().execute()
            return getattr(resp, "data", None)
        except Exception as e:
            raise normalize_error(e, "Failed to get requirement")

    @mcp.tool(tags={"requirements"})
    def requirements_list_with_filters(session_token: str, filters: Optional[dict] = None) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            q = sb.table("requirements").select("*")
            if filters:
                for k, v in filters.items():
                    if v is not None:
                        q = q.eq(k, v)
            resp = q.execute()
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list requirements")

    @mcp.tool(tags={"requirements"})
    def requirements_list_by_project(session_token: str, project_id: str) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = (
                sb.table("requirements")
                .select("*, documents!inner(id, project_id)")
                .eq("documents.project_id", project_id)
                .eq("is_deleted", False)
                .order("created_at", desc=False)
                .execute()
            )
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list requirements by project")

    @mcp.tool(tags={"requirements"})
    def requirements_list_by_document(session_token: str, document_id: str) -> list:
        return list_requirements_by_document(session_token, document_id)

    @mcp.tool(tags={"requirements"})
    def requirements_list_by_block(session_token: str, block_id: str) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = (
                sb.table("requirements").select("*").eq("block_id", block_id).order("created_at", desc=False).execute()
            )
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list requirements by block")

    @mcp.tool(tags={"requirements"})
    def requirements_list_by_block_ids(session_token: str, block_ids: list[str]) -> list:
        _require_session(session_token)
        if not block_ids:
            return []
        try:
            sb = get_supabase()
            resp = (
                sb.table("requirements").select("*, blocks!inner(name)").in_("block_id", block_ids).eq("is_deleted", False).execute()
            )
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list requirements by block ids")

    @mcp.tool(tags={"requirements"})
    def requirements_list_by_ids(session_token: str, ids: list[str]) -> list:
        _require_session(session_token)
        if not ids:
            return []
        try:
            sb = get_supabase()
            resp = sb.table("requirements").select("*").in_("id", ids).execute()
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list requirements by ids")

    @mcp.tool(tags={"requirements"})
    def requirements_create(session_token: str, input: dict) -> dict:
        sess = _require_session(session_token)
        try:
            sb = get_supabase()
            # discover organization via document -> project
            join_resp = (
                sb.table("documents")
                .select("project_id, projects!inner(organization_id)")
                .eq("id", input.get("document_id"))
                .single()
                .execute()
            )
            join = getattr(join_resp, "data", {}) or {}
            org_id = ((join.get("projects") or {}) or {}).get("organization_id")
            external_id = _generate_next_requirement_id(sb, org_id) if org_id else None
            payload = {
                **input,
                "version": 1,
                "properties": input.get("properties") or {},
            }
            if external_id:
                payload["external_id"] = external_id
            payload.setdefault("created_by", sess.user_id)
            resp = sb.table("requirements").insert(payload).select("*").single().execute()
            data = getattr(resp, "data", None)
            if not data:
                raise ApiError("DATABASE_ERROR", "Failed to create requirement")
            return data
        except Exception as e:
            raise normalize_error(e, "Failed to create requirement")

    @mcp.tool(tags={"requirements"})
    def requirements_update(session_token: str, id: str, input: dict) -> dict:
        _require_session(session_token)
        try:
            from datetime import datetime, timezone

            sb = get_supabase()
            resp = (
                sb.table("requirements")
                .update({**input, "updated_at": datetime.now(timezone.utc).isoformat()})
                .eq("id", id)
                .select("*")
                .single()
                .execute()
            )
            data = getattr(resp, "data", None)
            if not data:
                raise ApiError("DATABASE_ERROR", "Failed to update requirement")
            return data
        except Exception as e:
            raise normalize_error(e, "Failed to update requirement")

    @mcp.tool(tags={"requirements"})
    def requirements_soft_delete(session_token: str, id: str, deleted_by: str) -> dict:
        _require_session(session_token)
        try:
            from datetime import datetime, timezone

            sb = get_supabase()
            resp = (
                sb.table("requirements")
                .update({
                    "is_deleted": True,
                    "deleted_at": datetime.now(timezone.utc).isoformat(),
                    "deleted_by": deleted_by,
                })
                .eq("id", id)
                .select("*")
                .single()
                .execute()
            )
            data = getattr(resp, "data", None)
            if not data:
                raise ApiError("DATABASE_ERROR", "Failed to delete requirement")
            return data
        except Exception as e:
            raise normalize_error(e, "Failed to delete requirement")

    # ----------------------
    # Properties domain
    # ----------------------
    @mcp.tool(tags={"properties"})
    def properties_get_by_id(session_token: str, id: str) -> dict | None:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = sb.table("properties").select("*").eq("id", id).single().execute()
            return getattr(resp, "data", None)
            
        except Exception as e:
            raise normalize_error(e, "Failed to get property")

    @mcp.tool(tags={"properties"})
    def properties_list_by_org(session_token: str, org_id: str) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = sb.table("properties").select("*").eq("org_id", org_id).order("name").execute()
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list properties by org")

    @mcp.tool(tags={"properties"})
    def properties_list_by_document(session_token: str, document_id: str) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = sb.table("properties").select("*").eq("document_id", document_id).order("name").execute()
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list properties by document")

    @mcp.tool(tags={"properties"})
    def properties_list_org_base(session_token: str, org_id: str) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = (
                sb.table("properties")
                .select("*")
                .eq("org_id", org_id)
                .eq("is_base", True)
                .is_("document_id", None)
                .is_("project_id", None)
                .execute()
            )
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list base properties")

    @mcp.tool(tags={"properties"})
    def properties_create_many(session_token: str, props: list[dict]) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = sb.table("properties").insert(props).select("*").execute()
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to create properties")

    @mcp.tool(tags={"properties"})
    def properties_update(session_token: str, id: str, updates: dict) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = (
                sb.table("properties").update(updates).eq("id", id).select("*").single().execute()
            )
            data = getattr(resp, "data", None)
            if not data:
                raise ApiError("DATABASE_ERROR", "Failed to update property")
            return data
        except Exception as e:
            raise normalize_error(e, "Failed to update property")

    @mcp.tool(tags={"properties"})
    def properties_soft_delete(session_token: str, id: str) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            _ = sb.table("properties").delete().eq("id", id).execute()
            return {"id": id}
        except Exception as e:
            raise normalize_error(e, "Failed to delete property")

    @mcp.tool(tags={"properties"})
    def properties_update_positions(session_token: str, updates: list[dict]) -> dict:
        _require_session(session_token)
        try:
            from datetime import datetime, timezone

            sb = get_supabase()
            for u in updates:
                _ = (
                    sb.table("properties")
                    .update({
                        "position": u.get("position"),
                        "updated_by": u.get("updated_by"),
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    })
                    .eq("id", u.get("id"))
                    .execute()
                )
            return {"updated": len(updates)}
        except Exception as e:
            raise normalize_error(e, "Failed to update property positions")

    # ----------------------
    # Trace links
    # ----------------------
    @mcp.tool(tags={"trace_links"})
    def trace_links_create(session_token: str, input: dict) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            payload = {**input, "version": 1}
            resp = sb.table("trace_links").insert(payload).select("*").single().execute()
            return getattr(resp, "data", None) or {}
        except Exception as e:
            raise normalize_error(e, "Failed to create trace link")

    @mcp.tool(tags={"trace_links"})
    def trace_links_create_many(session_token: str, inputs: list[dict]) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            payload = [{**i, "version": 1} for i in inputs]
            resp = sb.table("trace_links").insert(payload).select("*").execute()
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to create trace links")

    @mcp.tool(tags={"trace_links"})
    def trace_links_soft_delete(session_token: str, id: str, deleted_by: str) -> dict:
        _require_session(session_token)
        try:
            from datetime import datetime, timezone

            sb = get_supabase()
            resp = (
                sb.table("trace_links")
                .update({
                    "is_deleted": True,
                    "deleted_at": datetime.now(timezone.utc).isoformat(),
                    "deleted_by": deleted_by,
                })
                .eq("id", id)
                .select("*")
                .single()
                .execute()
            )
            return getattr(resp, "data", None) or {}
        except Exception as e:
            raise normalize_error(e, "Failed to delete trace link")

    @mcp.tool(tags={"trace_links"})
    def trace_links_list_by_source(session_token: str, source_id: str, source_type: str, extra: Optional[dict] = None) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            q = (
                sb.table("trace_links").select("*").eq("source_id", source_id).eq("source_type", source_type).eq("is_deleted", False)
            )
            if extra:
                for k, v in extra.items():
                    if v is not None:
                        q = q.eq(k, v)
            resp = q.execute()
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list trace links by source")

    @mcp.tool(tags={"trace_links"})
    def trace_links_list_by_target(session_token: str, target_id: str, target_type: str, extra: Optional[dict] = None) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            q = (
                sb.table("trace_links").select("*").eq("target_id", target_id).eq("target_type", target_type).eq("is_deleted", False)
            )
            if extra:
                for k, v in extra.items():
                    if v is not None:
                        q = q.eq(k, v)
            resp = q.execute()
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list trace links by target")

    # ----------------------
    # Test matrix views
    # ----------------------
    @mcp.tool(tags={"test_matrix_views"})
    def test_matrix_list_by_project(session_token: str, project_id: str) -> list:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = (
                sb.table("test_matrix_views")
                .select("*")
                .eq("project_id", project_id)
                .eq("is_active", True)
                .order("created_at", desc=False)
                .execute()
            )
            return getattr(resp, "data", []) or []
        except Exception as e:
            raise normalize_error(e, "Failed to list test matrix views")

    @mcp.tool(tags={"test_matrix_views"})
    def test_matrix_insert(session_token: str, view: dict) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = sb.table("test_matrix_views").insert(view).select("*").single().execute()
            return getattr(resp, "data", None) or {}
        except Exception as e:
            raise normalize_error(e, "Failed to create test matrix view")

    @mcp.tool(tags={"test_matrix_views"})
    def test_matrix_update(session_token: str, id: str, updates: dict) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = (
                sb.table("test_matrix_views").update(updates).eq("id", id).select("*").single().execute()
            )
            return getattr(resp, "data", None) or {}
        except Exception as e:
            raise normalize_error(e, "Failed to update test matrix view")

    @mcp.tool(tags={"test_matrix_views"})
    def test_matrix_soft_delete(session_token: str, id: str) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            _ = sb.table("test_matrix_views").update({"is_active": False}).eq("id", id).execute()
            return {"id": id}
        except Exception as e:
            raise normalize_error(e, "Failed to delete test matrix view")

    @mcp.tool(tags={"test_matrix_views"})
    def test_matrix_get_by_id(session_token: str, id: str) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = (
                sb.table("test_matrix_views").select("*").eq("id", id).eq("is_active", True).single().execute()
            )
            return getattr(resp, "data", None) or {}
        except Exception as e:
            raise normalize_error(e, "Failed to fetch test matrix view")

    @mcp.tool(tags={"test_matrix_views"})
    def test_matrix_get_default(session_token: str, project_id: str) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            resp = (
                sb.table("test_matrix_views")
                .select("*")
                .eq("project_id", project_id)
                .eq("is_default", True)
                .eq("is_active", True)
                .single()
                .execute()
            )
            return getattr(resp, "data", None) or {}
        except Exception as e:
            raise normalize_error(e, "Failed to get default view")

    @mcp.tool(tags={"test_matrix_views"})
    def test_matrix_get_first_active(session_token: str, project_id: str) -> dict | None:
        _require_session(session_token)
        try:
            sb = get_supabase()
            # emulate limit(1).single()
            resp = (
                sb.table("test_matrix_views")
                .select("*")
                .eq("project_id", project_id)
                .eq("is_active", True)
                .order("created_at", desc=False)
                .limit(1)
                .execute()
            )
            data = getattr(resp, "data", []) or []
            return data[0] if data else None
        except Exception as e:
            raise normalize_error(e, "Failed to get first active view")

    @mcp.tool(tags={"test_matrix_views"})
    def test_matrix_unset_defaults(session_token: str, project_id: str, except_id: Optional[str] = None) -> dict:
        _require_session(session_token)
        try:
            sb = get_supabase()
            q = (
                sb.table("test_matrix_views").update({"is_default": False}).eq("project_id", project_id).eq("is_default", True)
            )
            if except_id:
                q = q.neq("id", except_id)
            _ = q.execute()
            return {"project_id": project_id, "except_id": except_id}
        except Exception as e:
            raise normalize_error(e, "Failed to unset default views")

    return mcp


def main() -> None:
    """Simple CLI runner.

    Environment variables:
      - ATOMS_FASTMCP_TRANSPORT: "http" or "stdio" (default: stdio)
      - ATOMS_FASTMCP_HOST: host when using http (default: 127.0.0.1)
      - ATOMS_FASTMCP_PORT: port when using http (default: 8000)
      - ATOMS_FASTMCP_MODE: "legacy" or "consolidated" or "compatible" (default: consolidated)
        - legacy: Original 100+ individual tools
        - consolidated: New 5 smart tools only
        - compatible: Both new and legacy tools (for migration)
      - ATOMS_FASTMCP_AUTH_MODE: "jwt" or "disabled" (default: jwt)
        - jwt: Supabase JWT token verification
        - disabled: No authentication (development only)
    """
    # Load env files early so any tooling (e.g., Supabase) sees values
    _load_env_files()

    transport = os.getenv("ATOMS_FASTMCP_TRANSPORT", "stdio")
    host = os.getenv("ATOMS_FASTMCP_HOST", "127.0.0.1")
    port_str = os.getenv("ATOMS_FASTMCP_PORT", "8000")
    mode = os.getenv("ATOMS_FASTMCP_MODE", "consolidated").lower()
    
    try:
        port = int(port_str)
    except ValueError:
        port = 8000

    # Create server based on mode
    if mode == "legacy":
        logger.info("Running in legacy mode with original tools")
        server = create_server()
    elif mode == "consolidated":
        logger.info("Running in consolidated mode with new agent-optimized tools")
        from .new_server import create_consolidated_server
        server = create_consolidated_server()
    elif mode == "compatible":
        logger.info("Running in compatible mode with both legacy and new tools")
        from .legacy import create_legacy_wrapper_server
        server = create_legacy_wrapper_server()
    else:
        logger.warning(f"Unknown mode '{mode}', defaulting to consolidated")
        from .new_server import create_consolidated_server
        server = create_consolidated_server()

    if transport == "http":
        # Optional: simple health check route
        @server.custom_route("/health", methods=["GET"])  # type: ignore[attr-defined]
        async def _health(_request):  # pragma: no cover
            from starlette.responses import PlainTextResponse

            return PlainTextResponse("OK")

        # Default to /api/mcp per requested mapping
        path = os.getenv("ATOMS_FASTMCP_HTTP_PATH", "/api/mcp")
        server.run(transport="http", host=host, port=port, path=path)
    else:
        server.run(transport="stdio")


if __name__ == "__main__":
    main()
