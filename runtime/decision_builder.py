from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from runtime.memory_resolvers import (
    resolve_name,
    resolve_favorite_color,
    resolve_favorite_food,
    resolve_previous_message,
    resolve_history_summary,
    resolve_profile_summary,
)
from runtime.memory_write_parser import parse_memory_write


DecisionMode = Literal["deterministic", "llm_assisted", "hybrid", "fallback"]
NoteSource = Literal["router", "resolver", "synthesis", "builder"]
NoteKind = Literal["match", "fallback", "empty", "info"]


@dataclass
class NoteEntry:
    source: NoteSource
    kind: NoteKind
    text: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "kind": self.kind,
            "text": self.text,
        }


@dataclass
class InputsMap:
    profile: bool = False
    memory: bool = False
    history: bool = False

    def to_dict(self) -> Dict[str, bool]:
        return {
            "profile": self.profile,
            "memory": self.memory,
            "history": self.history,
        }


@dataclass
class ResolverInfo:
    used: bool = False
    name: Optional[str] = None
    source: Optional[str] = None
    found: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "used": self.used,
            "name": self.name,
            "source": self.source,
            "found": self.found,
        }


@dataclass
class SynthesisInfo:
    used: bool = False
    name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "used": self.used,
            "name": self.name,
        }


@dataclass
class ResponsePlan:
    response_style: str = "direct"
    template_family: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "response_style": self.response_style,
            "template_family": self.template_family,
        }


@dataclass
class DecisionRequest:
    decision_type: str
    capability: str
    selected_path: str

    route: str
    route_family: str
    matched_by: str
    priority: int

    inputs_available: InputsMap
    inputs_used: InputsMap

    resolver: ResolverInfo = field(default_factory=ResolverInfo)
    synthesis: SynthesisInfo = field(default_factory=SynthesisInfo)
    response_plan: ResponsePlan = field(default_factory=ResponsePlan)
    notes: List[NoteEntry] = field(default_factory=list)

    decision_mode: DecisionMode = "deterministic"
    confidence: float = 1.0
    payload: Dict[str, Any] = field(default_factory=dict, repr=False)

    # default fields must stay after non-default fields
    target_office: Optional[str] = None
    handoff_reason: Optional[str] = None


@dataclass
class DecisionObject:
    decision_id: str
    decision_timestamp: str

    decision_type: str
    decision_mode: DecisionMode
    capability: str

    route: str
    route_family: str
    matched_by: str
    priority: int
    selected_path: str

    inputs_available: InputsMap
    inputs_used: InputsMap

    resolver: ResolverInfo
    synthesis: SynthesisInfo
    response_plan: ResponsePlan

    confidence: float
    notes: List[NoteEntry]

    payload: Dict[str, Any] = field(default_factory=dict, repr=False)

    # default fields must stay after non-default fields
    target_office: Optional[str] = None
    handoff_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "decision_timestamp": self.decision_timestamp,
            "decision_type": self.decision_type,
            "decision_mode": self.decision_mode,
            "capability": self.capability,
            "route": self.route,
            "route_family": self.route_family,
            "matched_by": self.matched_by,
            "priority": self.priority,
            "selected_path": self.selected_path,
            "target_office": self.target_office,
            "handoff_reason": self.handoff_reason,
            "inputs_available": self.inputs_available.to_dict(),
            "inputs_used": self.inputs_used.to_dict(),
            "resolver": self.resolver.to_dict(),
            "synthesis": self.synthesis.to_dict(),
            "response_plan": self.response_plan.to_dict(),
            "confidence": self.confidence,
            "notes": [n.to_dict() for n in self.notes],
        }


def build_decision_object(req: DecisionRequest) -> DecisionObject:
    return DecisionObject(
        decision_id=str(uuid4()),
        decision_timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        decision_type=req.decision_type,
        decision_mode=req.decision_mode,
        capability=req.capability,
        route=req.route,
        route_family=req.route_family,
        matched_by=req.matched_by,
        priority=req.priority,
        selected_path=req.selected_path,
        inputs_available=req.inputs_available,
        inputs_used=req.inputs_used,
        resolver=req.resolver,
        synthesis=req.synthesis,
        response_plan=req.response_plan,
        confidence=req.confidence,
        notes=req.notes,
        payload=req.payload,
        target_office=req.target_office,
        handoff_reason=req.handoff_reason,
    )


def _source_from_selected_path(selected_path: str) -> Optional[str]:
    if selected_path.endswith("_profile"):
        return "profile"
    if selected_path.endswith("_memory"):
        return "memory"
    if selected_path.endswith("_history"):
        return "history"
    return None


def _infer_target_office(text: str) -> str:
    t = (text or "").strip().lower()

    if not t:
        return "FRONTDESK"

    if any(x in t for x in ["pay", "payment", "invoice", "bill", "billing"]):
        return "BILLING"

    if any(x in t for x in ["service", "pricing", "quote", "interested", "contact me", "lead", "sales"]):
        return "SALES"

    return "FRONTDESK"


def build_fallback_decision(
    *,
    route: str = "default_answer",
    route_family: str = "fallback",
    matched_by: str = "builder_fallback",
    priority: int = 999,
    selected_path: str = "default",
    text: str = "",
) -> DecisionObject:
    return build_decision_object(
        DecisionRequest(
            decision_type="answer",
            capability="answer",
            selected_path=selected_path,
            route=route,
            route_family=route_family,
            matched_by=matched_by,
            priority=priority,
            inputs_available=InputsMap(),
            inputs_used=InputsMap(),
            resolver=ResolverInfo(used=False, name=None, source=None, found=False),
            synthesis=SynthesisInfo(used=False, name=None),
            response_plan=ResponsePlan(
                response_style="direct",
                template_family="fallback_answer",
            ),
            notes=[
                NoteEntry(
                    source="builder",
                    kind="fallback",
                    text=f"fallback decision generated for text={text!r}",
                )
            ],
            decision_mode="fallback",
            confidence=1.0,
            payload={},
            target_office=_infer_target_office(text),
            handoff_reason=None,
        )
    )


def build_decision(runtime_ctx: Dict[str, Any], routing: Dict[str, Any]) -> DecisionObject:
    profile = runtime_ctx.get("profile") or {}
    memory_items = (runtime_ctx.get("memory") or {}).get("items") or []
    history = (runtime_ctx.get("continuity") or {}).get("history") or []
    text = ((runtime_ctx.get("current_turn") or {}).get("text") or "").strip()

    route = routing.get("route", "default_answer")
    route_family = routing.get("family", "fallback")
    matched_by = routing.get("matched_by", "detector_default")
    priority = int(routing.get("priority", 10))
    route_capability = routing.get("capability") or "answer"

    inputs_available = InputsMap(
        profile=bool(profile),
        memory=bool(memory_items),
        history=bool(history),
    )

    base_notes = [
        NoteEntry(
            source="router",
            kind="match",
            text=f"matched by {matched_by}",
        )
    ]

    target_office = _infer_target_office(text)

    if route == "empty":
        return build_decision_object(
            DecisionRequest(
                decision_type="greeting",
                capability="greeting",
                selected_path="empty_input",
                route=route,
                route_family=route_family,
                matched_by=matched_by,
                priority=priority,
                inputs_available=inputs_available,
                inputs_used=InputsMap(),
                resolver=ResolverInfo(),
                synthesis=SynthesisInfo(),
                response_plan=ResponsePlan(
                    response_style="direct",
                    template_family="greeting",
                ),
                notes=base_notes,
                payload={"reply_kind": "empty_greeting"},
                target_office="FRONTDESK",
                handoff_reason=None,
            )
        )

    if route == "greeting":
        return build_decision_object(
            DecisionRequest(
                decision_type="greeting",
                capability="greeting",
                selected_path="greeting",
                route=route,
                route_family=route_family,
                matched_by=matched_by,
                priority=priority,
                inputs_available=inputs_available,
                inputs_used=InputsMap(),
                resolver=ResolverInfo(),
                synthesis=SynthesisInfo(),
                response_plan=ResponsePlan(
                    response_style="direct",
                    template_family="greeting",
                ),
                notes=base_notes,
                payload={"reply_kind": "greeting"},
                target_office="FRONTDESK",
                handoff_reason=None,
            )
        )

    if route == "profile_query":
        r = resolve_profile_summary(profile, memory_items)
        source = _source_from_selected_path(r["selected_path"])
        return build_decision_object(
            DecisionRequest(
                decision_type="profile_summary",
                capability="profile_summary",
                selected_path=r["selected_path"],
                route=route,
                route_family=route_family,
                matched_by=matched_by,
                priority=priority,
                inputs_available=inputs_available,
                inputs_used=InputsMap(
                    profile=bool(r["profile_used"]),
                    memory=bool(r["memory_used"]),
                    history=bool(r["history_used"]),
                ),
                resolver=ResolverInfo(
                    used=True,
                    name="resolve_profile_summary",
                    source=source,
                    found=bool(r["found"]),
                ),
                synthesis=SynthesisInfo(
                    used=bool(r["found"]),
                    name="synthesize_profile_summary" if r["found"] else None,
                ),
                response_plan=ResponsePlan(
                    response_style="direct",
                    template_family="profile_summary",
                ),
                notes=base_notes,
                payload={"result": r},
                target_office=target_office,
                handoff_reason=None,
            )
        )

    if route == "memory_write":
        parsed = parse_memory_write(text)
        matched = bool(parsed.get("matched"))
        return build_decision_object(
            DecisionRequest(
                decision_type="memory_write_ack",
                capability=route_capability,
                selected_path=parsed.get("selected_path", "memory_write_generic"),
                route=route,
                route_family=route_family,
                matched_by=matched_by,
                priority=priority,
                inputs_available=inputs_available,
                inputs_used=InputsMap(),
                resolver=ResolverInfo(
                    used=True,
                    name="parse_memory_write",
                    source="input_text",
                    found=matched,
                ),
                synthesis=SynthesisInfo(used=False, name=None),
                response_plan=ResponsePlan(
                    response_style="direct",
                    template_family="memory_write_ack",
                ),
                notes=base_notes if matched else base_notes + [
                    NoteEntry(
                        source="builder",
                        kind="fallback",
                        text="memory write parser did not match; using generic ack",
                    )
                ],
                payload={"parsed": parsed, "text": text},
                target_office=target_office,
                handoff_reason=None,
            )
        )

    if route == "name_recall":
        r = resolve_name(profile, memory_items)
        source = _source_from_selected_path(r["selected_path"])
        return build_decision_object(
            DecisionRequest(
                decision_type="memory_recall",
                capability="name_recall",
                selected_path=r["selected_path"],
                route=route,
                route_family=route_family,
                matched_by=matched_by,
                priority=priority,
                inputs_available=inputs_available,
                inputs_used=InputsMap(
                    profile=bool(r["profile_used"]),
                    memory=bool(r["memory_used"]),
                    history=bool(r["history_used"]),
                ),
                resolver=ResolverInfo(
                    used=True,
                    name="resolve_name",
                    source=source,
                    found=bool(r["found"]),
                ),
                synthesis=SynthesisInfo(),
                response_plan=ResponsePlan(
                    response_style="direct",
                    template_family="memory_recall",
                ),
                notes=base_notes,
                payload={"result": r},
                target_office=target_office,
                handoff_reason=None,
            )
        )

    if route == "favorite_color_recall":
        r = resolve_favorite_color(profile, memory_items)
        source = _source_from_selected_path(r["selected_path"])
        return build_decision_object(
            DecisionRequest(
                decision_type="memory_recall",
                capability="favorite_color_recall",
                selected_path=r["selected_path"],
                route=route,
                route_family=route_family,
                matched_by=matched_by,
                priority=priority,
                inputs_available=inputs_available,
                inputs_used=InputsMap(
                    profile=bool(r["profile_used"]),
                    memory=bool(r["memory_used"]),
                    history=bool(r["history_used"]),
                ),
                resolver=ResolverInfo(
                    used=True,
                    name="resolve_favorite_color",
                    source=source,
                    found=bool(r["found"]),
                ),
                synthesis=SynthesisInfo(),
                response_plan=ResponsePlan(
                    response_style="direct",
                    template_family="memory_recall",
                ),
                notes=base_notes,
                payload={"result": r},
                target_office=target_office,
                handoff_reason=None,
            )
        )

    if route == "favorite_food_recall":
        r = resolve_favorite_food(profile, memory_items)
        source = _source_from_selected_path(r["selected_path"])
        return build_decision_object(
            DecisionRequest(
                decision_type="memory_recall",
                capability="favorite_food_recall",
                selected_path=r["selected_path"],
                route=route,
                route_family=route_family,
                matched_by=matched_by,
                priority=priority,
                inputs_available=inputs_available,
                inputs_used=InputsMap(
                    profile=bool(r["profile_used"]),
                    memory=bool(r["memory_used"]),
                    history=bool(r["history_used"]),
                ),
                resolver=ResolverInfo(
                    used=True,
                    name="resolve_favorite_food",
                    source=source,
                    found=bool(r["found"]),
                ),
                synthesis=SynthesisInfo(),
                response_plan=ResponsePlan(
                    response_style="direct",
                    template_family="memory_recall",
                ),
                notes=base_notes,
                payload={"result": r},
                target_office=target_office,
                handoff_reason=None,
            )
        )

    if route == "previous_message":
        r = resolve_previous_message(history)
        return build_decision_object(
            DecisionRequest(
                decision_type="continuity_recall",
                capability="previous_message",
                selected_path=r["selected_path"],
                route=route,
                route_family=route_family,
                matched_by=matched_by,
                priority=priority,
                inputs_available=inputs_available,
                inputs_used=InputsMap(
                    profile=bool(r["profile_used"]),
                    memory=bool(r["memory_used"]),
                    history=bool(r["history_used"]),
                ),
                resolver=ResolverInfo(
                    used=True,
                    name="resolve_previous_message",
                    source="history",
                    found=bool(r["found"]),
                ),
                synthesis=SynthesisInfo(
                    used=bool(r["found"]),
                    name="synthesize_previous_message" if r["found"] else None,
                ),
                response_plan=ResponsePlan(
                    response_style="direct",
                    template_family="continuity_recall",
                ),
                notes=base_notes,
                payload={"result": r},
                target_office=target_office,
                handoff_reason=None,
            )
        )

    if route == "history_summary":
        r = resolve_history_summary(history)
        return build_decision_object(
            DecisionRequest(
                decision_type="conversation_summary",
                capability="conversation_summary",
                selected_path=r["selected_path"],
                route=route,
                route_family=route_family,
                matched_by=matched_by,
                priority=priority,
                inputs_available=inputs_available,
                inputs_used=InputsMap(
                    profile=bool(r["profile_used"]),
                    memory=bool(r["memory_used"]),
                    history=bool(r["history_used"]),
                ),
                resolver=ResolverInfo(
                    used=True,
                    name="resolve_history_summary",
                    source="history",
                    found=bool(r["found"]),
                ),
                synthesis=SynthesisInfo(
                    used=bool(r["found"]),
                    name="synthesize_history_summary" if r["found"] else None,
                ),
                response_plan=ResponsePlan(
                    response_style="direct",
                    template_family="conversation_summary",
                ),
                notes=base_notes,
                payload={"result": r},
                target_office=target_office,
                handoff_reason=None,
            )
        )

    return build_fallback_decision(
        route=route,
        route_family=route_family,
        matched_by=matched_by,
        priority=priority,
        selected_path="default",
        text=text,
    )