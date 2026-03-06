import logging
import os
from typing import Optional

from ppt_gen.deck_generator import DeckGenerator
from ppt_gen.docx_reader import parse_docx
from ppt_gen.info_reducer import InfoReducer
from ppt_gen.models import DayData, ProposalData
from ppt_gen.proposal_parser import parse_proposal
from ppt_gen.quote_service import QuoteService

logger = logging.getLogger(__name__)


class PPTService:

    def __init__(self, groq_api_key: Optional[str] = None):
        key = groq_api_key or os.environ.get("GROQ_API_KEY")
        if not key:
            raise ValueError(
                "Groq API key required. Set GROQ_API_KEY environment variable "
                "or pass groq_api_key= to PPTService()."
            )
        self.reducer = InfoReducer(api_key=key)
        self.quote_svc = QuoteService(api_key=key)
        self.deck_gen = DeckGenerator()


    def _build_what_creates(
        self, proposal: ProposalData
    ) -> dict:
        results = {}
        pos = proposal.picture_of_success

        if proposal.pre_retreat:
            results["pre_retreat"] = self.reducer.generate_what_this_creates(
                "At-Home Pre-Retreat", proposal.pre_retreat, pos
            )

        for day in proposal.days:
            results[f"day_{day.day_number}"] = self.reducer.generate_what_this_creates(
                f"Day {day.day_number}", day, pos
            )

        if proposal.post_retreat:
            results["post_retreat"] = self.reducer.generate_what_this_creates(
                "At-Home Integration & Phase II Support", proposal.post_retreat, pos
            )

        return results

    def generate_from_proposal(
        self,
        proposal: ProposalData,
        output_path: Optional[str] = None,
    ) -> bytes:
        logger.info("Starting PPT generation for client: %s", proposal.client_names)

        logger.info("Deriving day themes...")
        proposal = self.reducer.reduce_proposal(proposal)

        logger.info("Generating quotes...")
        quotes = self.quote_svc.generate_all_quotes(proposal)

        logger.info("Summarizing POS bullets from proposal...")
        pattern_bullets = self.reducer._summarize_long_bullets(
            proposal.picture_of_success, max_chars=60
        )

        logger.info("Generating 'What This Creates' bullets...")
        what_creates = self._build_what_creates(proposal)

        logger.info("Building PowerPoint deck...")
        pptx_bytes = self.deck_gen.generate(
            proposal=proposal,
            quotes=quotes,
            pattern_bullets=pattern_bullets,
            what_creates=what_creates,
            output_path=output_path,
        )

        logger.info(
            "PPT generation complete: %d slides, %d bytes",
            14,
            len(pptx_bytes),
        )
        return pptx_bytes

    def generate_from_markdown(
        self,
        markdown: str,
        output_path: Optional[str] = None,
    ) -> bytes:
        logger.info("Parsing proposal markdown...")
        proposal = parse_proposal(markdown)
        return self.generate_from_proposal(proposal, output_path=output_path)

    def generate_from_file(
        self,
        proposal_path: str,
        output_path: Optional[str] = None,
    ) -> bytes:
        ext = os.path.splitext(proposal_path)[1].lower()

        if ext == ".docx":
            logger.info("Reading Word document: %s", proposal_path)
            proposal = parse_docx(proposal_path)
            return self.generate_from_proposal(proposal, output_path=output_path)

        elif ext in (".md", ".txt", ""):
            logger.info("Reading markdown file: %s", proposal_path)
            with open(proposal_path, "r", encoding="utf-8") as f:
                markdown = f.read()
            return self.generate_from_markdown(markdown, output_path=output_path)

        else:
            raise ValueError(
                f"Unsupported file type: {ext!r}. Use .md or .docx."
            )


if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if len(sys.argv) < 2:
        print("Usage: python -m ppt_gen.ppt_service <proposal.md|proposal.docx> [output.pptx]")
        sys.exit(1)

    md_path = sys.argv[1]
    ext = os.path.splitext(md_path)[1].lower()
    default_out = md_path[: -len(ext)] + ".pptx" if ext else md_path + ".pptx"
    out_path = sys.argv[2] if len(sys.argv) > 2 else default_out

    service = PPTService()
    service.generate_from_file(md_path, output_path=out_path)
    print(f"Saved: {out_path}")
