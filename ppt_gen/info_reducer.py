
import json
import logging
import os
from typing import List

from groq import Groq

from ppt_gen.models import DayData, ProposalData, ReducedSection
from ppt_gen.prompts import (
    SYSTEM_CONDENSE_MODALITIES,
    SYSTEM_DAY_THEME,
    SYSTEM_INFO_REDUCE,
    SYSTEM_PATTERN_BULLETS,
    SYSTEM_SUMMARIZE_BULLETS,
    SYSTEM_WHAT_THIS_CREATES,
    USER_CONDENSE_MODALITIES,
    USER_DAY_THEME,
    USER_INFO_REDUCE,
    USER_PATTERN_BULLETS,
    USER_SUMMARIZE_BULLETS,
    USER_WHAT_THIS_CREATES,
)

logger = logging.getLogger(__name__)

MODEL = "llama-3.3-70b-versatile"


def _groq_json(client: Groq, system: str, user: str, temperature: float = 0.6, max_tokens: int = 1024) -> dict:
 
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        raw = response.choices[0].message.content.strip()
        raw = raw.strip("`").strip()
        if raw.startswith("json"):
            raw = raw[4:].strip()
        return json.loads(raw)
    except Exception as exc:
        logger.warning("Groq call failed: %s", exc)
        return {}


def _day_to_text(day: DayData) -> str:
    lines = []
    for s in day.sessions:
        lines.append(f"Session: {s.title}")
        if s.description:
            lines.append(f"  Description: {s.description}")
        if s.modalities:
            lines.append(f"  Modalities: {s.modalities}")
    return "\n".join(lines)


def _pos_to_text(pos: List[str]) -> str:
    return "\n".join(f"- {b}" for b in pos)


class InfoReducer:

    def __init__(self, api_key: str | None = None):
        key = api_key or os.environ.get("GROQ_API_KEY")
        if not key:
            raise ValueError("GROQ_API_KEY not set and no api_key provided.")
        self.client = Groq(api_key=key)


    @staticmethod
    def _fallback_condense(combined: str, max_terms: int = 5) -> str:

        terms = [t.strip() for t in combined.split(",") if t.strip()]
        seen = set()
        unique = []
        for t in terms:
            key = t.lower()
            if key not in seen:
                seen.add(key)
                unique.append(t)
        return ", ".join(unique[:max_terms])

    def condense_modalities(self, combined: str) -> str:

        if not combined or len(combined) < 60:
            return combined
        user = USER_CONDENSE_MODALITIES.format(modalities_text=combined)
        result = _groq_json(self.client, SYSTEM_CONDENSE_MODALITIES, user)
        condensed = result.get("modalities", "").strip()
        if condensed:
            return condensed
        return self._fallback_condense(combined)


    def derive_day_theme(self, day: DayData) -> str:
        user = USER_DAY_THEME.format(
            day_number=day.day_number,
            sessions_text=_day_to_text(day),
        )
        result = _groq_json(self.client, SYSTEM_DAY_THEME, user)
        theme = result.get("theme", "").strip()
        return theme or f"Day {day.day_number} Healing"


    def generate_what_this_creates(
        self, section_name: str, day: DayData, pos: List[str]
    ) -> List[str]:
        user = USER_WHAT_THIS_CREATES.format(
            section_name=section_name,
            sessions_text=_day_to_text(day),
            pos_text=_pos_to_text(pos) if pos else "Not provided",
        )
        result = _groq_json(self.client, SYSTEM_WHAT_THIS_CREATES, user)
        bullets = result.get("bullets", [])
        if not bullets:
            return [
                "✓ Creates safety for honest, regulated conversation",
                "✓ Interrupts old reactive patterns before they escalate",
                "✓ Builds shared tools you can use at home",
            ]
        return bullets[:4]


    def _summarize_long_bullets(self, bullets: List[str], max_chars: int = 80) -> List[str]:
        long_indices = [i for i, b in enumerate(bullets) if len(b) > max_chars]
        if not long_indices:
            return bullets

        long_bullets = [bullets[i] for i in long_indices]
        bullets_text = "\n".join(f"{i+1}. {b}" for i, b in enumerate(long_bullets))

        user = USER_SUMMARIZE_BULLETS.format(bullets_text=bullets_text)
        result = _groq_json(self.client, SYSTEM_SUMMARIZE_BULLETS, user, max_tokens=1024)
        shortened = result.get("bullets", [])

        if len(shortened) == len(long_indices):
            out = list(bullets)
            for idx, short in zip(long_indices, shortened):
                out[idx] = short.strip()
            return out

        logger.warning("Summarize call returned wrong count — returning original bullets without truncation")
        return bullets

    def generate_pattern_bullets(self, pos: List[str]) -> List[str]:
        fallback = [
            "To feel truly heard before either of you shuts down",
            "To stop the same argument from hijacking every week",
            "To reconnect emotionally without it feeling forced",
            "To trust that repair is possible after conflict",
            "To feel like teammates again, not opponents",
            "To love each other without walking on eggshells",
        ]
        if not pos:
            return fallback

        user = USER_PATTERN_BULLETS.format(pos_text=_pos_to_text(pos))
        result = _groq_json(self.client, SYSTEM_PATTERN_BULLETS, user, max_tokens=512)
        bullets = result.get("bullets", [])

        if len(bullets) == 6:
            return bullets

        logger.warning(
            "Pattern-bullet prompt returned %d bullets (expected 6) — falling back to summarize",
            len(bullets),
        )
        return self._summarize_long_bullets(pos, max_chars=80)

    def reduce_section(self, section_name: str, content: str) -> ReducedSection:
        user = USER_INFO_REDUCE.format(
            section_name=section_name,
            content=content,
        )
        result = _groq_json(self.client, SYSTEM_INFO_REDUCE, user)
        return ReducedSection(
            section_name=section_name,
            original_content=content,
            reduced_bullets=result.get("bullets", []),
            key_emotions=result.get("key_emotions", []),
            key_patterns=result.get("key_patterns", []),
        )


    def reduce_proposal(self, proposal: ProposalData) -> ProposalData:

        if proposal.pre_retreat and proposal.pre_retreat.combined_modalities:
            proposal.pre_retreat.combined_modalities = self.condense_modalities(
                proposal.pre_retreat.combined_modalities
            )

        for day in proposal.days:
            if not day.theme:
                day.theme = self.derive_day_theme(day)
                logger.info("Day %d theme: %s", day.day_number, day.theme)
            if day.combined_modalities:
                day.combined_modalities = self.condense_modalities(day.combined_modalities)
                logger.info("Day %d modalities condensed", day.day_number)

        if proposal.post_retreat and proposal.post_retreat.combined_modalities:
            proposal.post_retreat.combined_modalities = self.condense_modalities(
                proposal.post_retreat.combined_modalities
            )

        return proposal
