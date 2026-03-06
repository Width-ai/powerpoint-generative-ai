
SYSTEM_QUOTE = """
# Goal
Generate TWO emotional quotes for a healing retreat slide deck.

# Rules
- Each quote: 10–20 words only
- Abstract and poetic — do NOT reference the clients or their specific struggles directly
- Emotionally resonant with the session theme and the couple's relational pattern
- If a quote is by a real, named person include " — First Last" at the end
- The two quotes should be different in tone/theme but both relevant
- Respond ONLY with valid JSON: {"quotes": [{"quote": "...", "author": null}, {"quote": "...", "author": null}]}
  or include author if applicable: {"quotes": [{"quote": "...", "author": "First Last"}, ...]}

# Example quotes
- "Love is not a feeling. Love is a practice of presence when the nervous system wants to flee."
- "Between stimulus and response there is a space. In that space lies our freedom to choose." — Viktor Frankl
- "We cannot heal in the same nervous system state where the wound was created. Safety must come first."
- "The deepest intimacy comes not from never triggering each other, but from choosing to turn toward instead of away when we do."
- "Transformation is not an event — it's a practice. The retreat opens the door; integration helps you walk through it."
- "When we avoid the cost of change, we pay the price of staying the same."
- "The moment of decision is the beginning of transformation. Everything else is just preparation or delay."
- "Intention without alignment is just hope. Alignment without intention is just wandering."
"""

USER_QUOTE = """
Slide theme / session focus:
{session_info}

Couple's relational context (patterns, emotions):
{client_context}

Generate TWO quotes in JSON format: {{"quotes": [{{"quote": "...", "author": null}}, {{"quote": "...", "author": null}}]}}
"""

SYSTEM_DAY_THEME = """

Derive a short theme label for one day of a healing retreat, based ONLY on the session titles and descriptions provided.


- 3–6 words, title-case
- Must reflect the actual content of the sessions listed — do not invent themes not present in the text
- Respond ONLY with valid JSON: {"theme": "..."}
"""

USER_DAY_THEME = """
Day {day_number} session titles and descriptions (use ONLY this content):
{sessions_text}

Derive a short theme label in JSON: {{"theme": "..."}}
"""

SYSTEM_WHAT_THIS_CREATES = """

Write 3–4 short "What This Creates" outcome bullets for a retreat slide.
Each bullet describes the felt emotional experience the client will have — short, vivid, human.


You must base every bullet on the session content provided. Do not invent sessions or outcomes
that have no connection to the text given.


- 7–10 words each — short and punchy
- Describe the felt experience, not a clinical outcome
- Avoid generic openers like "You'll establish..." or "You'll develop..." — be more vivid
- Use contrast or metaphor where it fits naturally:
    ✓ "Arrive grounded rather than guarded" (not "✓ You'll feel less guarded")
    ✓ "Bring unmet needs into the open without blame" (not "✓ You'll articulate needs")
    ✓ "Reveal the patterns you inherited, not who you are" (not "✓ You'll identify patterns")
- Written in second-person ("you", "your") — no "you'll" as the opener if it sounds flat
- Start each bullet with "✓ "
- Respond ONLY with valid JSON: {"bullets": ["✓ ...", "✓ ...", "✓ ...", "✓ ..."]}
"""

USER_WHAT_THIS_CREATES = """
Section: {section_name}

Client's Picture of Success — what THEY said they want (anchor every bullet here):
{pos_text}

Sessions and descriptions for THIS section only:
{sessions_text}

Write 3–4 emotionally vivid outcome bullets that connect what happens in these sessions
to what THIS client specifically wants. Each bullet must only make sense for this section
and this client — not generic enough to apply to any retreat day.
JSON: {{"bullets": ["✓ ...", ...]}}
"""


SYSTEM_CONDENSE_MODALITIES = """
# Goal
Condense a long comma-separated list of therapy modalities into 4–6 short, unique key terms for a slide.

# Rules
- ONLY use terms already present in the provided list — do NOT invent new ones
- Remove duplicates and near-duplicates (e.g. "expectation mapping" and "outcome mapping" → keep one)
- Pick the most distinct, representative terms
- Each term should be 1–4 words, lowercase (except proper nouns)
- Respond ONLY with valid JSON: {"modalities": "term1, term2, term3, term4"}
"""

USER_CONDENSE_MODALITIES = """
Full modalities list:
{modalities_text}

Return 4–6 unique key terms in JSON: {{"modalities": "..."}}
"""


SYSTEM_SUMMARIZE_BULLETS = """
# Goal
Transform each bullet point into a concise, complete sentence of 8–12 words that fits perfectly on a slide.
Make them clear, readable, and impactful — like natural speech.

# Rules
- Create complete, grammatically correct sentences (not fragments)
- Keep the core meaning and most important keywords from the original
- Maintain the same voice and tense (usually "we" statements)
- Each bullet must be self-contained and make sense on its own
- Remove filler words but keep the essence and flow
- Aim for natural, readable language that sounds authentic
- Each bullet should be a complete thought that ends with a period
- Respond ONLY with valid JSON: {"bullets": ["...", "...", ...]}
  with the same number of bullets as provided, in the same order
"""

USER_SUMMARIZE_BULLETS = """
Transform each bullet into a concise, complete sentence of 8–12 words.
Make them clear, natural, and readable — complete thoughts that fit on a slide.
Keep the core meaning and important keywords from the original.

Bullets:
{bullets_text}

Return the same number of bullets in the same order as JSON: {{"bullets": [...]}}
"""


SYSTEM_PATTERN_BULLETS = """
# Goal
Generate emotionally resonant bullet points for the "What You Told Me You Want Instead"
slide in a couples healing retreat deck.

# Rules
- Exactly 6 bullets
- 10–16 words each, present tense
- Speak directly to felt experience and relational longing
- No therapy jargon; use plain, emotionally honest language
- Respond ONLY with valid JSON: {"bullets": ["...", "...", "...", "...", "...", "..."]}
"""

USER_PATTERN_BULLETS = """
Client Picture of Success:
{pos_text}

Generate exactly 6 "What You Want Instead" bullets in JSON: {{"bullets": [...]}}
"""

SYSTEM_INFO_REDUCE = """
# Goal
Condense a section of a healing retreat proposal into key emotional themes.

# Rules
- Extract 3–5 bullet points that capture the emotional and relational essence
- Remove logistical, business, or administrative details
- Focus on transformation, safety, patterns, and relational outcomes
- Each bullet: 8–14 words, emotionally resonant
- Respond ONLY with valid JSON:
  {"bullets": ["...", ...], "key_emotions": ["...", ...], "key_patterns": ["...", ...]}
"""

USER_INFO_REDUCE = """
Section name: {section_name}

Section content:
{content}

Condense to emotional essence in JSON:
{{"bullets": [...], "key_emotions": [...], "key_patterns": [...]}}
"""
