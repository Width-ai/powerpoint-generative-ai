from typing import List
from pptx import Presentation
from pptx.slide import Slide
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Inches
from powerpoint_generative_ai.utils.utils import setup_logger


SLIDE_LAYOUTS = {
    "Title Slide": 0,
    "Title and Content": 1,
    "Section Header": 2,
    "Two Content": 3,
    "Comparison": 4,
    "Title Only": 5,
    "Blank": 6,
    "Content with Caption": 7,
    "Picture with Caption": 8,
}


class PowerPointCreator:
    def __init__(self, title: str, slides_content: List[dict]):
        self.title = title
        self.slides_content = slides_content
        self.presentation = Presentation()
        self.logger = setup_logger(__name__)


    def create(self, file_name: str = 'presentation.pptx'):
        """Creates powerpoint and saves it to specified filename"""
        slide_layout = self.presentation.slide_layouts[0] 
        slide = self.presentation.slides.add_slide(slide_layout)
        title = slide.shapes.title
        title.text = self.title

        # Creating slides
        for content in self.slides_content:
            self.add_slide(content)

        self.save(file_name=file_name)


    def add_slide(self, content: dict):
        """Helper function to add slides to powerpoint"""
        text_content = content.get('content', None)
        chart_data = content.get('chart_data', None)
        LAYOUT = SLIDE_LAYOUTS['Title Slide']
        if chart_data and text_content:
            LAYOUT = SLIDE_LAYOUTS['Two Content'] # Text column and blank right side
        elif chart_data and not text_content:
            LAYOUT = SLIDE_LAYOUTS['Title Only'] # Just a title for a big chart
        elif text_content and not chart_data:
            LAYOUT = SLIDE_LAYOUTS['Title and Content'] # Standard slide format

        slide_layout = self.presentation.slide_layouts[LAYOUT]
        slide = self.presentation.slides.add_slide(slide_layout)
        title = slide.shapes.title
        title.text = content.get('title', None)

        if text_content:
            content_shape = slide.shapes.placeholders[1]
            content_shape.text = text_content
        
        if chart_data:
            self.add_chart(data=chart_data, slide=slide, chart_type=content.get('chart_type', XL_CHART_TYPE.COLUMN_CLUSTERED))


    def add_chart(self, data: dict, slide: Slide, x: Inches = Inches(4.75), y: Inches = Inches(2), cx: Inches=Inches(5.5), cy: Inches = Inches(4.5), chart_type: int = XL_CHART_TYPE.COLUMN_CLUSTERED):
        """Creates a chart and adds it to the current slide"""
        chart_data = CategoryChartData()
        chart_data.categories = data['categories']
        for series in data['series']:
            chart_data.add_series(series['name'], series['values'])

        chart = slide.shapes.add_chart(chart_type, x, y, cx, cy, chart_data).chart

        for series in chart.series:
            series.has_data_labels = True


    def save(self, file_name: str):
        self.presentation.save(file_name)
        self.logger.info(f"Presentation successfully created: {file_name}")

