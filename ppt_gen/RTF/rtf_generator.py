from typing import List, Optional

from ppt_gen.models import DayData, ProposalData, Quote

CONTENT_W = 9360
COL_HALF = CONTENT_W // 2


def _esc(text: str) -> str:
    result = []
    for ch in text:
        if ch == '\\':
            result.append('\\\\')
        elif ch == '{':
            result.append('\\{')
        elif ch == '}':
            result.append('\\}')
        elif ch == '\r':
            pass
        elif ch == '\n':
            result.append(' ')
        elif ord(ch) > 127:
            code = ord(ch)
            signed = code if code <= 32767 else code - 65536
            result.append(f'\\u{signed}?')
        else:
            result.append(ch)
    return ''.join(result)


class RTFGenerator:

    ORANGE = 1
    SAGE   = 2
    DARK   = 3
    WHITE  = 4
    CREAM  = 5
    MINT   = 6
    GOLD   = 7
    TEAL   = 8

    def generate(
        self,
        proposal: ProposalData,
        quotes: dict,
        pattern_bullets: List[str],
        what_creates: dict,
        output_path: Optional[str] = None,
    ) -> bytes:
        self._buf: List[str] = []
        self._rtf_header()

        self._write_title(proposal, quotes.get('title'))

        self._write_truth(quotes.get('truth'))
        self._write_what_you_want(pattern_bullets, quotes.get('pattern'))
        self._write_getting_in_way(quotes.get('getting_in_way'))
        self._write_how_retreat(quotes.get('how_retreat'))
        self._write_journey(quotes.get('journey'))

        if proposal.pre_retreat:
            self._write_day(
                'AT-HOME PRE-RETREAT', 'Pre-Retreat Intention Setting',
                proposal.pre_retreat,
                quotes.get('pre_retreat'), what_creates.get('pre_retreat', []),
            )
        else:
            self._section_header_card('AT-HOME PRE-RETREAT')
            self._section_break()

        for i in range(4):
            if i < len(proposal.days):
                day = proposal.days[i]
                theme = day.theme or f'Day {day.day_number}'
                self._write_day(
                    f'DAY {day.day_number}', theme,
                    day,
                    quotes.get(f'day_{day.day_number}'),
                    what_creates.get(f'day_{day.day_number}', []),
                )
            else:
                self._section_header_card(f'DAY {i + 1}')
                self._section_break()

        if proposal.post_retreat:
            self._write_day(
                'AT-HOME INTEGRATION & PHASE II SUPPORT', '12-Month Follow-Up',
                proposal.post_retreat,
                quotes.get('post_retreat'), what_creates.get('post_retreat', []),
            )
        else:
            self._section_header_card('AT-HOME INTEGRATION & PHASE II SUPPORT')
            self._section_break()

        self._write_investment(
            proposal.investment_amount or '$0',
            proposal.investment_details,
            quotes.get('investment'),
        )

        self._write_next_step(quotes.get('next_step'))

        self._w('}\n')

        content = ''.join(self._buf).encode('ascii', errors='replace')
        if output_path:
            with open(output_path, 'wb') as fh:
                fh.write(content)
        return content

    def _rtf_header(self) -> None:
        self._w(
            '{\\rtf1\\ansi\\ansicpg1252\\deff0\n'
            '{\\fonttbl\n'
            '{\\f0\\fnil\\fcharset0 Wulkan Display Medium;}\n'
            '{\\f1\\fnil\\fcharset0 Inter;}\n'
            '}\n'
            '{\\colortbl;\n'
            '\\red172\\green78\\blue39;\n'
            '\\red134\\green150\\blue127;\n'
            '\\red43\\green43\\blue43;\n'
            '\\red255\\green255\\blue255;\n'
            '\\red242\\green229\\blue223;\n'
            '\\red237\\green241\\blue235;\n'
            '\\red201\\green160\\blue74;\n'
            '\\red31\\green78\\blue94;\n'
            '}\n'
            '\\widowctrl\\hyphauto\n'
            '\\margl1440\\margr1440\\margt1440\\margb1440\n'
        )

    def _w(self, s: str) -> None:
        self._buf.append(s)

    def _gap(self) -> None:
        self._w('\\pard\\sa160\\par\n')

    def _gap_sm(self) -> None:
        self._w('\\pard\\sa80\\par\n')

    def _section_break(self) -> None:
        self._w('\\pard\\page\\par\n')

    def _section_header_card(self, title: str) -> None:
        self._w(
            f'\\trowd\\trgaph0\\trleft0'
            f'\\trpaddl200\\trpaddt160\\trpaddr200\\trpaddb160\n'
            f'\\clcbpat{self.ORANGE}'
            f'\\clbrdrl\\brdrnil\\clbrdrt\\brdrnil'
            f'\\clbrdrr\\brdrnil\\clbrdrb\\brdrnil'
            f'\\cellx{CONTENT_W}\n'
            f'\\pard\\intbl\\f0\\fs52\\cf{self.WHITE}\\b {_esc(title)}\\b0'
            f'\\cell\n\\row\\pard\n'
        )

    def _day_header_card(self, day_label: str, theme: str) -> None:
        self._w(
            f'\\trowd\\trgaph0\\trleft0'
            f'\\trpaddl200\\trpaddt160\\trpaddr200\\trpaddb160\n'
            f'\\clcbpat{self.ORANGE}'
            f'\\clbrdrl\\brdrnil\\clbrdrt\\brdrnil'
            f'\\clbrdrr\\brdrnil\\clbrdrb\\brdrnil'
            f'\\cellx{CONTENT_W}\n'
            f'\\pard\\intbl\\f0\\fs52\\cf{self.WHITE}\\b {_esc(day_label)}\\b0'
            f'\\par\\f0\\fs30\\cf{self.WHITE}\\b {_esc(theme)}\\b0'
            f'\\cell\n\\row\\pard\n'
        )

    def _quote_box(self, text: str) -> None:
        self._w(
            f'\\trowd\\trgaph0\\trleft0'
            f'\\trpaddl360\\trpaddt160\\trpaddr360\\trpaddb160\n'
            f'\\clcbpat{self.MINT}'
            f'\\clbrdrl\\brdrw60\\brdrs\\brdrcf{self.SAGE}'
            f'\\clbrdrt\\brdrnil\\clbrdrr\\brdrnil\\clbrdrb\\brdrnil'
            f'\\cellx{CONTENT_W}\n'
            f'\\pard\\intbl\\qc\\f1\\fs22\\cf{self.SAGE}\\i {_esc(text)}\\i0\\cell\n'
            f'\\row\\pard\n'
        )

    def _say_box(self, text: str) -> None:
        self._w(
            f'\\trowd\\trgaph0\\trleft0'
            f'\\trpaddl200\\trpaddt100\\trpaddr200\\trpaddb100\n'
            f'\\clcbpat{self.MINT}'
            f'\\clbrdrl\\brdrw40\\brdrs\\brdrcf{self.SAGE}'
            f'\\clbrdrt\\brdrnil\\clbrdrr\\brdrnil\\clbrdrb\\brdrnil'
            f'\\cellx{CONTENT_W}\n'
            f'\\pard\\intbl\\f1\\fs20\\cf{self.SAGE}\\i {_esc(text)}\\i0\\cell\n'
            f'\\row\\pard\n'
        )

    def _amount_box(self, text: str) -> None:
        self._w(
            f'\\trowd\\trgaph0\\trleft0'
            f'\\trpaddl200\\trpaddt200\\trpaddr200\\trpaddb200\n'
            f'\\clcbpat{self.DARK}'
            f'\\clbrdrl\\brdrnil\\clbrdrt\\brdrnil'
            f'\\clbrdrr\\brdrnil\\clbrdrb\\brdrnil'
            f'\\cellx{CONTENT_W}\n'
            f'\\pard\\intbl\\f0\\fs80\\cf{self.WHITE}\\b {_esc(text)}\\b0\\cell\n'
            f'\\row\\pard\n'
        )

    def _h2(self, text: str) -> None:
        self._w(
            f'\\pard\\sb200\\sa60'
            f'\\brdrb\\brdrw10\\brdrs\\brdrcf{self.SAGE}'
            f'\\f0\\fs32\\cf{self.ORANGE}\\b {_esc(text)}\\b0\\par\n'
        )

    def _body(self, text: str) -> None:
        self._w(f'\\pard\\sa100\\f1\\fs24\\cf{self.DARK} {_esc(text)}\\par\n')

    def _bullet(self, text: str) -> None:
        clean = text.lstrip('\u2022\u25c6\u2713-* ').strip()
        self._w(
            f'\\pard\\li360\\fi-360\\sa80'
            f'\\f1\\fs22\\cf{self.DARK} \\u8226? {_esc(clean)}\\par\n'
        )

    def _label(self, text: str) -> None:
        self._w(
            f'\\pard\\sa60\\f0\\fs22\\cf{self.SAGE}\\b {_esc(text)}\\b0\\par\n'
        )

    def _day_two_col(self, day: DayData, what_creates: List[str]) -> None:
        C1 = COL_HALF
        C2 = CONTENT_W

        self._w(
            f'\\trowd\\trgaph0\\trleft0'
            f'\\trbrdrl\\brdrnil\\trbrdrt\\brdrnil'
            f'\\trbrdrr\\brdrnil\\trbrdrb\\brdrnil'
            f'\\trbrdrh\\brdrnil\\trbrdrv\\brdrnil'
            f'\\trpaddl0\\trpaddt120\\trpaddr0\\trpaddb200\n'
            f'\\clbrdrl\\brdrnil\\clbrdrt\\brdrnil'
            f'\\clbrdrr\\brdrnil\\clbrdrb\\brdrnil'
            f'\\cellx{C1}\n'
            f'\\clbrdrl\\brdrw12\\brdrs\\brdrcf{self.GOLD}'
            f'\\clbrdrt\\brdrnil\\clbrdrr\\brdrnil\\clbrdrb\\brdrnil'
            f'\\cellx{C2}\n'
        )

        left = []

        left.append(
            f'\\pard\\intbl'
            f'\\brdrb\\brdrw12\\brdrs\\brdrcf{self.GOLD}'
            f'\\sb0\\sa60'
            f'\\f0\\fs22\\cf{self.TEAL}\\b SESSIONS\\b0'
        )

        for s in day.sessions:
            left.append(
                f'\\pard\\intbl\\li200\\fi-200'
                f'\\sb40\\sa40'
                f'\\f1\\fs22\\cf{self.DARK}'
                f' {{\\cf{self.GOLD}\\u8226?}} {_esc(s.title)}'
            )

        left.append(
            f'\\pard\\intbl'
            f'\\brdrb\\brdrw12\\brdrs\\brdrcf{self.GOLD}'
            f'\\sb120\\sa60'
            f'\\f0\\fs22\\cf{self.TEAL}\\b MODALITIES\\b0'
        )

        if day.combined_modalities:
            left.append(
                f'\\pard\\intbl'
                f'\\sb40\\sa40'
                f'\\f1\\fs20\\cf{self.SAGE}\\i {_esc(day.combined_modalities)}\\i0'
            )
        else:
            left.append(f'\\pard\\intbl\\f1\\fs20\\cf{self.SAGE} ')

        self._w('\\par\n'.join(left) + '\\cell\n')

        right = []

        right.append(
            f'\\pard\\intbl\\li200'
            f'\\brdrb\\brdrw12\\brdrs\\brdrcf{self.GOLD}'
            f'\\sb0\\sa60'
            f'\\f0\\fs22\\cf{self.TEAL}\\b WHAT THIS CREATES\\b0'
        )

        for b in what_creates:
            clean = b.lstrip('\u2713\u2022\u25c6-* ').strip()
            right.append(
                f'\\pard\\intbl\\li200'
                f'\\sb40\\sa40'
                f'\\f1\\fs22\\cf{self.DARK}'
                f' {{\\cf{self.TEAL}\\u10003?}} {_esc(clean)}'
            )

        if len(right) == 1:
            right.append(f'\\pard\\intbl\\li200\\f1\\fs22\\cf{self.DARK} ')

        self._w('\\par\n'.join(right) + '\\cell\n')

        self._w('\\row\\pard\n')

    def _how_retreat_two_col(self) -> None:
        C1 = COL_HALF
        C2 = CONTENT_W

        self._w(
            f'\\trowd\\trgaph0\\trleft0'
            f'\\trbrdrl\\brdrnil\\trbrdrt\\brdrnil'
            f'\\trbrdrr\\brdrnil\\trbrdrb\\brdrnil'
            f'\\trbrdrh\\brdrnil\\trbrdrv\\brdrnil'
            f'\\trpaddl0\\trpaddt120\\trpaddr0\\trpaddb200\n'
            f'\\clbrdrl\\brdrnil\\clbrdrt\\brdrnil'
            f'\\clbrdrr\\brdrnil\\clbrdrb\\brdrnil'
            f'\\cellx{C1}\n'
            f'\\clbrdrl\\brdrw12\\brdrs\\brdrcf{self.GOLD}'
            f'\\clbrdrt\\brdrnil\\clbrdrr\\brdrnil\\clbrdrb\\brdrnil'
            f'\\cellx{C2}\n'
        )

        left = []
        left.append(
            f'\\pard\\intbl'
            f'\\brdrb\\brdrw12\\brdrs\\brdrcf{self.GOLD}'
            f'\\sb0\\sa60'
            f'\\f0\\fs22\\cf{self.TEAL}\\b REGULATION & SAFETY\\b0'
        )
        left.append(
            f'\\pard\\intbl\\sb40\\sa80'
            f'\\f1\\fs22\\cf{self.DARK}'
            f' {_esc("Calm the nervous system so conversations don\u2019t spiral automatically")}'
        )
        left.append(
            f'\\pard\\intbl'
            f'\\brdrb\\brdrw12\\brdrs\\brdrcf{self.GOLD}'
            f'\\sb120\\sa60'
            f'\\f0\\fs22\\cf{self.TEAL}\\b CORE PATTERN REPAIR\\b0'
        )
        left.append(
            f'\\pard\\intbl\\sb40\\sa40'
            f'\\f1\\fs22\\cf{self.DARK}'
            f' {_esc("Heal the root dynamic driving repeated conflict")}'
        )
        self._w('\\par\n'.join(left) + '\\cell\n')

        right = []
        right.append(
            f'\\pard\\intbl\\li200'
            f'\\brdrb\\brdrw12\\brdrs\\brdrcf{self.GOLD}'
            f'\\sb0\\sa60'
            f'\\f0\\fs22\\cf{self.TEAL}\\b INTEGRATION & FORWARD PATH\\b0'
        )
        right.append(
            f'\\pard\\intbl\\li200\\sb40\\sa40'
            f'\\f1\\fs22\\cf{self.DARK}'
            f' {_esc("Build shared tools that actually work at home")}'
        )
        self._w('\\par\n'.join(right) + '\\cell\n')

        self._w('\\row\\pard\n')

    def _fmt_quote(self, q: Quote) -> str:
        text = f'\u201c{q.text}\u201d'
        if q.author:
            text += f'  \u2014 {q.author}'
        return text

    def _get_quotes(self, quotes) -> List[str]:
        if not quotes:
            return []
        if isinstance(quotes, list):
            return [self._fmt_quote(q) for q in quotes if q]
        return [self._fmt_quote(quotes)]

    def _write_title(self, proposal: ProposalData, quotes) -> None:
        qs = self._get_quotes(quotes)
        lines = proposal.retreat_title.split('\n')
        title_rtf = '\\line '.join(_esc(l) for l in lines)
        self._w(
            f'\\pard\\qc\\sb600\\sa200\\f0\\fs80\\cf{self.ORANGE}\\b '
            f'{title_rtf}\\b0\\par\n'
        )
        self._w(
            f'\\pard\\qc\\sa160\\f0\\fs56\\cf{self.ORANGE} '
            f'{_esc(proposal.client_names)}\\par\n'
        )
        if proposal.date:
            self._w(
                f'\\pard\\qc\\sa200\\f1\\fs28\\cf{self.SAGE} '
                f'{_esc(proposal.date)}\\par\n'
            )
        self._w(
            f'\\pard\\sb200\\sa200'
            f'\\brdrb\\brdrw25\\brdrs\\brdrcf{self.ORANGE}'
            f'\\f1\\fs2\\cf3  \\par\n'
        )
        for qt in qs[:2]:
            self._quote_box(qt)
        self._gap_sm()
        self._section_break()

    def _write_truth(self, quotes) -> None:
        qs = self._get_quotes(quotes)
        self._section_header_card('THE TRUTH ABOUT YOUR PATTERN')
        if qs:
            self._gap_sm()
            self._quote_box(qs[0])
        self._gap()
        self._body('This isn\u2019t about fixing one of you.')
        self._gap_sm()
        self._body('It\u2019s about changing the pattern that keeps pulling you apart.')
        self._gap()
        self._say_box(
            'Say: \u201cBefore we talk about logistics or sessions, I want to ground us '
            'in what this retreat is actually designed to change.\u201d'
        )
        self._section_break()

    def _write_what_you_want(self, bullets: List[str], quotes) -> None:
        qs = self._get_quotes(quotes)
        self._section_header_card('WHAT YOU TOLD ME YOU WANT INSTEAD')
        if qs:
            self._gap_sm()
            self._quote_box(qs[0])
        self._gap()
        for b in bullets:
            self._bullet(b)
        if len(qs) >= 2:
            self._gap()
            self._quote_box(qs[1])
        self._section_break()

    def _write_getting_in_way(self, quotes) -> None:
        qs = self._get_quotes(quotes)
        self._section_header_card('WHAT\u2019S ACTUALLY GETTING IN THE WAY')
        if qs:
            self._gap_sm()
            self._quote_box(qs[0])
        self._gap()
        self._h2('The Real Issue:')
        self._bullet('You\u2019re reacting from old nervous-system patterns, not the present moment')
        self._bullet('Conversations escalate before either of you feels fully heard')
        self._bullet('You\u2019ve never been given tools to interrupt the cycle together')
        self._gap()
        self._body('This isn\u2019t a communication problem.')
        self._body('It\u2019s a regulation + pattern problem.')
        self._gap()
        self._say_box(
            'Say: \u201cMost couples try to talk their way out of a nervous-system issue. '
            'That\u2019s why insight alone hasn\u2019t been enough.\u201d'
        )
        self._section_break()

    def _write_how_retreat(self, quotes) -> None:
        qs = self._get_quotes(quotes)
        self._section_header_card('HOW THIS RETREAT CREATES CHANGE')
        if qs:
            self._gap_sm()
            self._quote_box(qs[0])
        self._gap()
        self._how_retreat_two_col()
        self._gap()
        self._say_box(
            'Say: \u201cEvery session fits into one of these three categories. '
            'Nothing here is random or extra.\u201d'
        )
        self._section_break()

    def _write_journey(self, quotes) -> None:
        qs = self._get_quotes(quotes)
        self._section_header_card('YOUR TRANSFORMATION JOURNEY')
        if qs:
            self._gap_sm()
            self._quote_box(qs[0])
        self._gap()
        self._body('Let me walk you through exactly what happens \u2014 and why each piece matters')
        if len(qs) >= 2:
            self._gap()
            self._quote_box(qs[1])
        self._section_break()

    def _write_day(
        self,
        day_label: str,
        theme: str,
        day: DayData,
        quotes,
        what_creates: List[str],
    ) -> None:
        qs = self._get_quotes(quotes)
        self._day_header_card(day_label, theme)
        if qs:
            self._gap_sm()
            self._quote_box(qs[0])
        self._gap_sm()
        self._day_two_col(day, what_creates)
        self._section_break()

    def _write_investment(
        self, amount: str, details: List[str], quotes,
    ) -> None:
        qs = self._get_quotes(quotes)
        self._section_header_card('YOUR INVESTMENT IN TRANSFORMATION')
        if qs:
            self._gap_sm()
            self._quote_box(qs[0])
        self._gap()
        amount_text = (
            f'Total Investment: {amount}'
            if not amount.startswith('Total Investment') else amount
        )
        self._w(
            f'\\pard\\sb100\\sa100\\f0\\fs28\\cf{self.DARK}\\b {_esc(amount_text)}\\b0\\par\n'
        )
        if details:
            self._gap()
            self._label('Payment Options:')
            for line in details:
                if line.strip():
                    self._bullet(line.strip())
        self._gap()
        self._body('This retreat is private, customized, and capacity-limited')
        if len(qs) >= 2:
            self._gap()
            self._quote_box(qs[1])
        self._section_break()

    def _write_next_step(self, quotes) -> None:
        qs = self._get_quotes(quotes)
        self._section_header_card('YOUR NEXT STEP')
        if qs:
            self._gap_sm()
            self._quote_box(qs[0])
        self._gap()
        self._body('If this feels aligned:')
        self._bullet('We secure your dates')
        self._bullet('Lock in your practitioner team for 12 months')
        self._bullet('Begin pre-retreat intention work')
        self._gap()
        self._w(
            f'\\trowd\\trgaph0\\trleft0'
            f'\\trpaddl200\\trpaddt140\\trpaddr200\\trpaddb140\n'
            f'\\clcbpat{self.CREAM}'
            f'\\clbrdrl\\brdrw20\\brdrs\\brdrcf{self.ORANGE}'
            f'\\clbrdrt\\brdrw20\\brdrs\\brdrcf{self.ORANGE}'
            f'\\clbrdrr\\brdrw20\\brdrs\\brdrcf{self.ORANGE}'
            f'\\clbrdrb\\brdrw20\\brdrs\\brdrcf{self.ORANGE}'
            f'\\cellx{CONTENT_W}\n'
            f'\\pard\\intbl\\qc\\f0\\fs30\\cf{self.ORANGE}\\b'
            f' Place your deposit today to hold availability'
            f'\\b0\\cell\n\\row\\pard\n'
        )
        self._gap()
        self._say_box(
            'Say: \u201cWhat questions do you need answered to feel clear about moving forward?\u201d'
        )