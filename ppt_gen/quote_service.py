
import json
import logging
import os
import re

from groq import Groq

from typing import List
from ppt_gen.models import DayData, ProposalData, Quote
from ppt_gen.prompts import SYSTEM_QUOTE, USER_QUOTE

logger = logging.getLogger(__name__)

MODEL = "llama-3.3-70b-versatile"

FALLBACK_QUOTES: dict[str, Quote] = {
    "title": Quote(
        text="The journey of transformation begins with a single step — the decision to choose something different."
    ),
    "truth": Quote(
        text="This isn't about fixing one of you. It's about changing the pattern that keeps pulling you apart."
    ),
    "pattern": Quote(
        text="Love is not a feeling. Love is a practice of presence when the nervous system wants to flee."
    ),
    "pre_retreat": Quote(
        text="Intention without alignment is just hope. Alignment without intention is just wandering."
    ),
    "day_1": Quote(
        text="We cannot heal in the same nervous system state where the wound was created. Safety must come first."
    ),
    "day_2": Quote(
        text="The body keeps the score — and it also holds the map back to wholeness.",
        author="Bessel van der Kolk (adapted)",
    ),
    "day_3": Quote(
        text="The deepest intimacy comes not from never triggering each other, but from choosing to turn toward instead of away."
    ),
    "day_4": Quote(
        text="Trust is rebuilt in the small moments of choosing presence over protection."
    ),
    "post_retreat": Quote(
        text="Transformation is not an event — it's a practice. The retreat opens the door; integration helps you walk through it."
    ),
    "investment": Quote(
        text="When we avoid the cost of change, we pay the price of staying the same."
    ),
    "next_step": Quote(
        text="The moment of decision is the beginning of transformation. Everything else is just preparation or delay."
    ),
}


def _call_groq(client: Groq, system: str, user: str) -> dict:
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.7,
            max_tokens=256,  
        )
        raw = response.choices[0].message.content.strip().strip("`")
        if raw.startswith("json"):
            raw = raw[4:].strip()

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        m = re.search(r'"quote"\s*:\s*"([^"]+)"', raw)
        if m:
            quote_text = m.group(1).strip()
            author_m = re.search(r'[—\-]{1,2}\s*([A-Z][a-zA-Z\s\.]+)(?:\s*[}\"]|$)', raw)
            author = author_m.group(1).strip() if author_m else None
            return {"quotes": [{"quote": quote_text, "author": author}]}

        logger.warning("Quote Groq response unparseable: %s", raw[:120])
        return {}
    except Exception as exc:
        logger.warning("Quote Groq call failed: %s", exc)
        return {}


class QuoteService:

    def __init__(self, api_key: str | None = None):
        key = api_key or os.environ.get("GROQ_API_KEY")
        if not key:
            raise ValueError("GROQ_API_KEY not set.")
        self.client = Groq(api_key=key)

    def _make_quotes(self, session_info: str, client_context: str, fallback_key: str) -> List[Quote]:
        user = USER_QUOTE.format(
            session_info=session_info,
            client_context=client_context,
        )
        result = _call_groq(self.client, SYSTEM_QUOTE, user)
        
        quotes_list = result.get("quotes", [])
        if not quotes_list or len(quotes_list) < 2:
            if "quote" in result:
                text = result.get("quote", "").strip()
                author = result.get("author") or None
                if text and len(text.split()) >= 8:
                    quotes_list = [{"quote": text, "author": author}]
            
            if len(quotes_list) < 2:
                logger.info("Using fallback quotes for key=%s", fallback_key)
                fallback = FALLBACK_QUOTES.get(fallback_key, FALLBACK_QUOTES["pattern"])
                fallback2 = FALLBACK_QUOTES.get("pattern")
                quotes_list = [
                    {"quote": fallback.text, "author": fallback.author},
                    {"quote": fallback2.text, "author": fallback2.author} if fallback2 != fallback else {"quote": fallback.text, "author": fallback.author}
                ]
        
        quotes = []
        for q in quotes_list[:2]:
            text = q.get("quote", "").strip() if isinstance(q, dict) else str(q).strip()
            author = q.get("author") if isinstance(q, dict) else None
            if text and len(text.split()) >= 8:
                quotes.append(Quote(text=text, author=author))
        
        while len(quotes) < 2:
            fallback = FALLBACK_QUOTES.get(fallback_key, FALLBACK_QUOTES["pattern"])
            quotes.append(Quote(text=fallback.text, author=fallback.author))
        
        return quotes[:2]

    def _pos_context(self, proposal: ProposalData) -> str:
        return "; ".join(proposal.picture_of_success[:4])

    def quote_for_title_slide(self, proposal: ProposalData) -> List[Quote]:
        return self._make_quotes(
            session_info="Title slide — opening slide for the proposal presentation",
            client_context=self._pos_context(proposal),
            fallback_key="title",
        )

    def quote_for_truth_slide(self, proposal: ProposalData) -> List[Quote]:
        return self._make_quotes(
            session_info="Truth about pattern slide — understanding that this isn't about fixing one person, but changing the pattern",
            client_context=self._pos_context(proposal),
            fallback_key="truth",
        )

    def quote_for_pattern_slide(self, proposal: ProposalData) -> List[Quote]:
        return self._make_quotes(
            session_info="What you want slide — the client's vision for their relationship transformation",
            client_context=self._pos_context(proposal),
            fallback_key="pattern",
        )

    def quote_for_pre_retreat(self, proposal: ProposalData) -> List[Quote]:
        return self._make_quotes(
            session_info="Pre-retreat intention setting — aligning as a couple before arriving",
            client_context=self._pos_context(proposal),
            fallback_key="pre_retreat",
        )

    def quote_for_day(self, day: DayData, proposal: ProposalData) -> List[Quote]:
        theme = day.theme or f"Day {day.day_number}"
        session_names = ", ".join(s.title for s in day.sessions)
        return self._make_quotes(
            session_info=f"Day {day.day_number} — {theme}. Sessions: {session_names}",
            client_context=self._pos_context(proposal),
            fallback_key=f"day_{day.day_number}",
        )

    def quote_for_post_retreat(self, proposal: ProposalData) -> List[Quote]:
        return self._make_quotes(
            session_info="Post-retreat integration — taking insights home and sustaining change",
            client_context=self._pos_context(proposal),
            fallback_key="post_retreat",
        )

    def quote_for_investment(self, proposal: ProposalData) -> List[Quote]:
        return self._make_quotes(
            session_info="Investment slide — the cost of change vs the cost of staying the same",
            client_context=self._pos_context(proposal),
            fallback_key="investment",
        )

    def quote_for_next_step(self, proposal: ProposalData) -> List[Quote]:
        return self._make_quotes(
            session_info="Next step / call-to-action slide — the moment of decision",
            client_context=self._pos_context(proposal),
            fallback_key="next_step",
        )

    def generate_all_quotes(self, proposal: ProposalData) -> dict[str, List[Quote]]:
        quotes: dict[str, List[Quote]] = {}
        quotes["title"] = self.quote_for_title_slide(proposal)
        quotes["truth"] = self.quote_for_truth_slide(proposal)
        quotes["pattern"] = self.quote_for_pattern_slide(proposal)
        quotes["pre_retreat"] = self.quote_for_pre_retreat(proposal)
        for day in proposal.days:
            quotes[f"day_{day.day_number}"] = self.quote_for_day(day, proposal)
        quotes["post_retreat"] = self.quote_for_post_retreat(proposal)
        quotes["investment"] = self.quote_for_investment(proposal)
        quotes["next_step"] = self.quote_for_next_step(proposal)
        logger.info("Generated %d quote sets (2 quotes each)", len(quotes))
        return quotes
