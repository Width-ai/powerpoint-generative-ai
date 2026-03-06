import re
import logging
from typing import List, Optional, Tuple

from docx import Document
from docx.oxml.ns import qn

from ppt_gen.models import DayData, ProposalData, Session

logger = logging.getLogger(__name__)


def _text(para) -> str:
    t = para.text.strip()
    t = t.replace("\u2019", "'").replace("\u2018", "'")
    t = t.replace("\u201c", '"').replace("\u201d", '"')
    t = t.replace("\u2013", "-").replace("\u2014", "-")
    t = t.replace("\u2026", "...")
    return t


def _is_list(para) -> bool:
    return para._element.find(f".//{qn('w:numPr')}") is not None


def _style(para) -> str:
    return (para.style.name if para.style else "").lower()


def _is_day_line(text: str) -> Optional[int]:
    m = re.match(r"^day\s+(\d)\s*$", text.strip(), re.IGNORECASE)
    return int(m.group(1)) if m else None


class _SectionAccumulator:

    def __init__(self, name: str):
        self.name = name
        self.paras: list = []

    def add(self, para):
        self.paras.append(para)

    def texts(self) -> List[str]:
        return [_text(p) for p in self.paras if _text(p)]

    def bullets(self) -> List[str]:
        return [_text(p) for p in self.paras if _is_list(p) and _text(p)]

    def body_lines(self) -> List[str]:
        return [_text(p) for p in self.paras
                if not _is_list(p) and _style(p) not in ("heading 2", "heading 3")
                and _text(p)]


def _parse_sessions(section: _SectionAccumulator) -> Tuple[List[Session], Optional[str]]:
    sessions: List[Session] = []
    combined_modalities: List[str] = []
    current_session: Optional[Session] = None
    desc_lines: List[str] = []

    def _flush():
        if current_session:
            current_session.description = " ".join(desc_lines).strip() or None
            sessions.append(current_session)

    for para in section.paras:
        t = _text(para)
        s = _style(para)

        if s == "heading 3":
            _flush()
            current_session = Session(title=t)
            desc_lines = []

        elif s in ("heading 2",):
            continue

        elif t:
            if current_session is None:
                continue

            mod_m = re.match(r"modalities?:\s*(.+)", t, re.IGNORECASE)
            if mod_m:
                mod_text = mod_m.group(1).strip()
                current_session.modalities = mod_text
                combined_modalities.append(mod_text)
            elif not t.startswith("("):
                desc_lines.append(t)

    _flush()

    combined = ", ".join(combined_modalities) if combined_modalities else None
    return sessions, combined


def parse_docx(path_or_stream) -> ProposalData:
    doc = Document(path_or_stream)
    paragraphs = doc.paragraphs

    sections: List[_SectionAccumulator] = []
    current: _SectionAccumulator = _SectionAccumulator("__preamble__")

    for para in paragraphs:
        t = _text(para)
        s = _style(para)

        if s == "heading 2" and t:
            sections.append(current)
            current = _SectionAccumulator(t.upper())
        elif s == "normal" and _is_day_line(t):
            sections.append(current)
            current = _SectionAccumulator(t.upper())
        else:
            current.add(para)

    sections.append(current)

    section_map: dict = {sec.name: sec for sec in sections}

    client_names = "Your Clients"
    date: Optional[str] = None

    for para in paragraphs:
        if _style(para) == "title":
            t = _text(para)
            if re.match(r"\d{1,2}/\d{1,2}/\d{4}", t):
                date = t
                continue
            nm = re.search(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+and\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", t)
            if nm:
                client_names = f"{nm.group(1)} & {nm.group(2)}"

    if client_names == "Your Clients":
        preamble_sec = section_map.get("__preamble__")
        if preamble_sec:
            for line in preamble_sec.body_lines():
                dm = re.search(r"Dear\s+([A-Z][a-z]+)\s+and\s+([A-Z][a-z]+)", line)
                if dm:
                    client_names = f"{dm.group(1)} & {dm.group(2)}"
                    break

    picture_of_success: List[str] = []
    preamble_sec = section_map.get("__preamble__")
    if preamble_sec:
        in_pos = False
        for para in preamble_sec.paras:
            t = _text(para)
            if "picture of success" in t.lower():
                in_pos = True
                continue
            if in_pos and t:
                picture_of_success.append(t)

    investment_amount: Optional[str] = None
    investment_details: List[str] = []

    inv_sec = next((s for s in sections if "investment" in s.name.lower()), None)
    if inv_sec:
        for line in inv_sec.body_lines():
            m = re.search(r"\$[\d,]+(?:\.\d{2})?", line)
            if m and not investment_amount:
                investment_amount = m.group(0)
        investment_details = inv_sec.bullets()

    how_retreat_works: List[str] = []
    how_sec = next((s for s in sections if "how this retreat" in s.name.lower()), None)
    if how_sec:
        how_retreat_works = how_sec.bullets() or how_sec.body_lines()

    pre_retreat: Optional[DayData] = None
    pre_sec = next(
        (s for s in sections if "pre-retreat" in s.name.lower() or "pre retreat" in s.name.lower()),
        None,
    )
    if pre_sec:
        pre_sessions, pre_mod = _parse_sessions(pre_sec)
        pre_retreat = DayData(
            day_number=0,
            theme="Pre-Retreat Intention Setting",
            sessions=pre_sessions,
            combined_modalities=pre_mod,
        )

    days: List[DayData] = []
    for day_num in range(1, 5):
        day_sec = section_map.get(f"DAY {day_num}")
        if day_sec is None:
            continue
        day_sessions, day_mod = _parse_sessions(day_sec)
        days.append(DayData(
            day_number=day_num,
            theme=None,
            sessions=day_sessions,
            combined_modalities=day_mod,
        ))

    post_retreat: Optional[DayData] = None
    post_sec = next(
        (s for s in sections if "post-retreat" in s.name.lower() or "post retreat" in s.name.lower()),
        None,
    )
    if post_sec:
        post_sessions, post_mod = _parse_sessions(post_sec)
        post_retreat = DayData(
            day_number=99,
            theme="At-Home Integration & Phase II Support",
            sessions=post_sessions,
            combined_modalities=post_mod,
        )

    logger.info(
        "Parsed docx: client=%s, days=%d, pos=%d",
        client_names, len(days), len(picture_of_success),
    )

    return ProposalData(
        client_names=client_names,
        date=date,
        picture_of_success=picture_of_success,
        investment_amount=investment_amount,
        investment_details=investment_details,
        how_retreat_works=how_retreat_works,
        pre_retreat=pre_retreat,
        days=days,
        post_retreat=post_retreat,
    )
