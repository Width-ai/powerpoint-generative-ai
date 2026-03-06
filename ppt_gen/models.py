
from typing import List, Optional
from dataclasses import dataclass, field


@dataclass
class Quote:
    text: str
    author: Optional[str] = None  


@dataclass
class Session:
    title: str
    modalities: Optional[str] = None
    description: Optional[str] = None


@dataclass
class DayData:
    day_number: int          
    theme: Optional[str] = None   
    sessions: List[Session] = field(default_factory=list)
    combined_modalities: Optional[str] = None   


@dataclass
class ProposalData:
    client_names: str
    retreat_title: str = "Transformational\nSoul Coach Training"
    date: Optional[str] = None
    picture_of_success: List[str] = field(default_factory=list)
    investment_amount: Optional[str] = None
    investment_details: List[str] = field(default_factory=list)
    how_retreat_works: List[str] = field(default_factory=list)
    pre_retreat: Optional["DayData"] = None     
    days: List[DayData] = field(default_factory=list)
    post_retreat: Optional["DayData"] = None    
    raw_markdown: Optional[str] = None


@dataclass
class ReducedSection:
    section_name: str           
    original_content: str
    reduced_bullets: List[str] = field(default_factory=list)  
    key_emotions: List[str] = field(default_factory=list)
    key_patterns: List[str] = field(default_factory=list)
    theme_label: Optional[str] = None   

@dataclass
class TwoColumnContent:
    sessions: List[str] = field(default_factory=list)
    modalities: Optional[str] = None
    what_this_creates: List[str] = field(default_factory=list)   


@dataclass
class SlideContent:
    slide_type: str             
    title: str
    subtitle: Optional[str] = None
    quote: Optional[Quote] = None
    body_lines: List[str] = field(default_factory=list)     
    bullet_points: List[str] = field(default_factory=list)  
    footer: Optional[str] = None
    two_col: Optional[TwoColumnContent] = None            

    investment_amount: Optional[str] = None
    payment_options: List[str] = field(default_factory=list)
    investment_note: Optional[str] = None
    
    cta: Optional[str] = None
    conditional: Optional[str] = None  


@dataclass
class Slide:
    order: int
    content: SlideContent
    
    background_color: str = "#000000"   
    title_color: str = "#C0504D"        
    body_color: str = "#806462"         
    quote_color: str = "#90A68A"        
    accent_color: str = "#E8E0D8"       


@dataclass
class PowerPointDeck:
    client_names: str
    slides: List[Slide] = field(default_factory=list)

    def add_slide(self, slide: Slide) -> None:
        self.slides.append(slide)

    def get_slides_by_type(self, slide_type: str) -> List[Slide]:
        return [s for s in self.slides if s.content.slide_type == slide_type]
