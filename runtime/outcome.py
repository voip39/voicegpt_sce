from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class OutcomeObject:
    """
    Canonical delivery contract between decision layer and channel layer.

    Phase 13B baseline:
      text          — primary reply for all channels
      short_text    — SMS-friendly (≤160 chars)
      speech_text   — TTS-friendly (no robotic prefix, no markdown)
      outcome_type  — mirrors decision_type
      template_family — mirrors decision.response_plan.template_family
      channel_hints — future channel-specific rendering hints
      meta          — debug / trace
    """

    # Core semantic content
    text: str

    # Channel-specific variants
    short_text: Optional[str] = None    # SMS-friendly
    speech_text: Optional[str] = None   # TTS-friendly

    # Metadata
    outcome_type: str = "reply"
    template_family: Optional[str] = None

    # Channel hints (not binding in 13B — used by renderers in 13C+)
    channel_hints: Dict[str, Any] = field(default_factory=dict)

    # Debug / trace
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text":            self.text,
            "short_text":      self.short_text,
            "speech_text":     self.speech_text,
            "outcome_type":    self.outcome_type,
            "template_family": self.template_family,
            "channel_hints":   self.channel_hints,
            "meta":            self.meta,
        }
