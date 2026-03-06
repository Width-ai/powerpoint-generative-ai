
import re
import logging
from typing import List, Optional, Tuple

from ppt_gen.models import ProposalData, DayData, Session

logger = logging.getLogger(__name__)


def _clean(text: str) -> str:
    text = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", text)
    text = re.sub(r"_{1,2}([^_]+)_{1,2}", r"\1", text)
    text = re.sub(r"\\(.)", r"\1", text)   
    return text.strip()


def _extract_bullet_list(block: str) -> List[str]:
    bullets = []
    for line in block.splitlines():
        m = re.match(r"^\s*[*\-●•]\s+(.+)", line)
        if m:
            bullets.append(_clean(m.group(1)))
    return bullets


def _split_sections(markdown: str) -> dict:

    sections: dict = {}
    current_heading = "__preamble__"
    current_lines: List[str] = []

    for line in markdown.splitlines():
        m = re.match(r"^#{1,2}\s+(.+)", line)
        m2 = None if m else re.match(r"^\*\*(DAY\s+\d+)\*\*\s*$", line.strip(), re.IGNORECASE)

        if m or m2:
            sections[current_heading] = "\n".join(current_lines).strip()
            heading_text = _clean(m.group(1)) if m else (m2.group(1) if m2 else "")
            current_heading = heading_text
            current_lines = []
        else:
            current_lines.append(line)

    sections[current_heading] = "\n".join(current_lines).strip()
    return sections


def _extract_pos_from_raw(markdown: str) -> List[str]:

    pos_match = re.search(r"Picture of Success[:\s]*", markdown, re.IGNORECASE)
    if not pos_match:
        return []
    block = markdown[pos_match.end():]
    next_section = re.search(r"^#{1,2}\s+", block, re.MULTILINE)
    if next_section:
        block = block[: next_section.start()]
    return _extract_bullet_list(block)


def _parse_sessions_from_block(block: str) -> Tuple[List[Session], str]:
    sessions: List[Session] = []
    combined_modalities: List[str] = []

    parts = re.split(r"###\s+", block)
    for part in parts:
        if not part.strip():
            continue
        lines = part.strip().splitlines()
        title = _clean(lines[0]) if lines else ""
        body = "\n".join(lines[1:]).strip()

        modalities = None
        description_lines = []
        for line in body.splitlines():
            mod_m = re.match(r"[*_]?Modalities?:\s*(.+)[*_]?", line, re.IGNORECASE)
            if mod_m:
                modalities = _clean(mod_m.group(1))
                if modalities:
                    combined_modalities.append(modalities)
            else:
                stripped = line.strip().lstrip("*_").strip()
                if stripped and not stripped.startswith("("):
                    description_lines.append(_clean(stripped))

        description = " ".join(description_lines).strip() or None
        if title:
            sessions.append(Session(
                title=title,
                modalities=modalities,
                description=description,
            ))

    combined = ", ".join(combined_modalities) if combined_modalities else None
    return sessions, combined


def _extract_client_names(preamble: str, full_markdown: str) -> str:

    m = re.search(
        r"#\s+\*?\*?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+and\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        full_markdown,
    )
    if m:
        return f"{m.group(1)} & {m.group(2)}"

    m = re.search(r"Dear\s+([A-Z][a-z]+)\s+and\s+([A-Z][a-z]+)", full_markdown)
    if m:
        return f"{m.group(1)} & {m.group(2)}"

    m = re.search(r"Dear\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),", full_markdown)
    if m:
        return m.group(1)

    return "Your Clients"


def _extract_date(full_markdown: str) -> Optional[str]:
    m = re.search(r"#\s+(\d{1,2}/\d{1,2}/\d{4})", full_markdown)
    return m.group(1) if m else None


def _extract_investment(block: str) -> Tuple[Optional[str], List[str]]:
    amount = None
    details: List[str] = []

    m = re.search(r"\$[\d,]+(?:\.\d{2})?", block)
    if m:
        amount = m.group(0)

    in_includes = False
    for line in block.splitlines():
        if "includes" in line.lower():
            in_includes = True
            continue
        if in_includes:
            bm = re.match(r"^\s*[*\-]\s+(.+)", line)
            if bm:
                details.append(_clean(bm.group(1)))
            elif line.strip() and not line.strip().startswith("#"):
                in_includes = False

    return amount, details


def parse_proposal(markdown: str) -> ProposalData:
    sections = _split_sections(markdown)

    preamble = sections.get("__preamble__", "")
    client_names = _extract_client_names(preamble, markdown)
    date = _extract_date(markdown)
    picture_of_success = _extract_pos_from_raw(markdown)
    if not picture_of_success:
        pos_block = ""
        for key in sections:
            if "picture of success" in key.lower() or key == "__preamble__":
                pos_block = sections[key]
        picture_of_success = _extract_bullet_list(pos_block)

    inv_block = ""
    for key in sections:
        if "investment" in key.lower():
            inv_block = sections[key]
            break
    investment_amount, investment_details = _extract_investment(inv_block)

    how_block = ""
    for key in sections:
        if "how this retreat works" in key.lower():
            how_block = sections[key]
            break
    how_retreat_works = _extract_bullet_list(how_block)

    pre_retreat: Optional[DayData] = None
    for key in sections:
        if "pre-retreat" in key.lower() or "pre retreat" in key.lower():
            pre_block = sections[key]
            pre_sessions, pre_modalities = _parse_sessions_from_block(pre_block)
            pre_retreat = DayData(
                day_number=0,
                theme="Pre-Retreat Intention Setting",
                sessions=pre_sessions,
                combined_modalities=pre_modalities,
            )
            break

    days: List[DayData] = []
    for day_num in range(1, 5):
        day_key = None
        for key in sections:
            if re.match(rf"^day\s*{day_num}\b", key.strip(), re.IGNORECASE):
                day_key = key
                break
        if day_key is None:
            continue
        day_block = sections[day_key]
        day_sessions, day_modalities = _parse_sessions_from_block(day_block)
        days.append(DayData(
            day_number=day_num,
            theme=None,
            sessions=day_sessions,
            combined_modalities=day_modalities,
        ))

    post_retreat: Optional[DayData] = None
    for key in sections:
        if "post-retreat" in key.lower() or "post retreat" in key.lower():
            post_block = sections[key]
            post_sessions, post_modalities = _parse_sessions_from_block(post_block)
            post_retreat = DayData(
                day_number=99,
                theme="At-Home Integration & Phase II Support",
                sessions=post_sessions,
                combined_modalities=post_modalities,
            )
            break

    logger.info(
        "Parsed proposal: client=%s, days=%d, pos_bullets=%d",
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
        raw_markdown=markdown,
    )
