
INTAKE_CALL_EXTRACTION = """
You are analyzing a transcription of an intake call. Chris is the interviewer — focus your analysis entirely on the other person (the client).

Extract the following from the conversation:

## Goals
What does the client want to achieve? What outcomes are they seeking? Include both explicitly stated goals and goals implied through context.

## Passions
What lights them up? What do they talk about with energy or excitement? What activities, topics, or visions do they gravitate toward naturally?

## Struggles
What challenges are they currently facing? What has been difficult for them? What patterns of difficulty do they describe?

## Emotional Barriers
What fears, doubts, or limiting beliefs surface during the conversation? Where do they hesitate, deflect, or show signs of internal resistance? Note any recurring emotional themes (e.g. fear of failure, imposter syndrome, guilt, overwhelm).

## Key Quotes
Pull 3-5 direct quotes from the client that are particularly revealing or meaningful. These should capture their voice and emotional state.

## Summary
Write a concise 2-3 paragraph profile of this person — who they are right now, what they're navigating, and what they most need support with.

---

Guidelines:
- Ignore Chris's words except as context for the client's responses.
- Read between the lines — pay attention to what is unsaid, minimized, or repeated.
- Use the client's own language whenever possible.
- Be empathetic but precise. This analysis will be used to tailor their coaching experience.

<transcript>
{transcript}
</transcript>
"""

