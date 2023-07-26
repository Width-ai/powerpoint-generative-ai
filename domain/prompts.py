DECK_CREATION_SYSTEM_PROMPT = """Take the user input and create content for a slideshow related to the user's input. You will generate titles for the slides, content that tells a cohesive story throughout the slides. DO NOT title each slide like 'Slide X: ...'.

Data may be provided in the input, if it has been provided determine the best slide to include a chart. ONLY INSERT CHARTS when data is provided.

Example input and output for your guidance:
User input: Create a 3 slide powerpoint as a test, include this data for a chart:
x axis: Jan, Feb, March, Apr, May, Jun, Jul
Series 1: 1, 2, 3, 4, 5, 6, 7
Series 2: 2, 3, 4, 5, 6, 7, 8
Series 3: 3, 4, 5, 6, 7, 8, 9

Use chart type: 4

Output:
[
    {
        'title': 'Slide 1',
        'content': 'This is some content for slide 1'
    },
    {
        'title': 'Slide 2',
        'content': 'This slide has a multi-line chart',
        'chart_data': {
            'categories': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
            'series': [
                {'name': 'Series 1', 'values': [1, 2, 3, 4, 5, 6, 7]},
                {'name': 'Series 2', 'values': [2, 3, 4, 5, 6, 7, 8]},
                {'name': 'Series 3', 'values': [3, 4, 5, 6, 7, 8, 9]}
            ]
        },
        'chart_type': 4
    },
    {
        'title': 'Slide 3',
        'content': 'This is some content for slide 3'
    }
]

Note: Your output must be parsable, valid JSON. DO NOT summarize what each slide was about, the content on each slide should be meaningful information"""


CHART_DATA_IDENTIFICATION = """Does the user text provide data to create a chart? If yes, say 'data found', if no say 'no data'"""


BEST_CHART_FOR_DATA_SYSTEM_PROMPT = """Is the user asking to use a specific type of chart in their request? If so return the value from the dictionary below, if not evaluate the data in the text and determine which chart would be best to use from this dictionary based on the descriptions. Only return the value of the most applicable chart type:

{
    "BAR_CLUSTERED": {"value": 57, "description": "Clustered Bar."},
    "BAR_OF_PIE": {"value": 71, "description": "Bar of Pie."},
    "BAR_STACKED": {"value": 58, "description": "Stacked Bar."},
    "BAR_STACKED_100": {"value": 59, "description": "100% Stacked Bar."},
    "COLUMN_CLUSTERED": {"value": 51, "description": "Clustered Column."},
    "COLUMN_STACKED": {"value": 52, "description": "Stacked Column."},
    "COLUMN_STACKED_100": {"value": 53, "description": "100% Stacked Column."},
    "LINE": {"value": 4, "description": "Line."},
    "LINE_MARKERS": {"value": 65, "description": "Line with Markers."},
    "LINE_MARKERS_STACKED": {"value": 66, "description": "Stacked Line with Markers."},
    "LINE_MARKERS_STACKED_100": {"value": 67, "description": "100% Stacked Line with Markers."},
    "LINE_STACKED": {"value": 63, "description": "Stacked Line."},
    "LINE_STACKED_100": {"value": 64, "description": "100% Stacked Line."},
}"""

TITLE_GEN_SYSTEM_PROMPT = """Generate a title for this powerpoint based on the content"""

FILENAME_SYSTEM_PROMPT = """Take the powerpoint title in the user text and create a short version to be used as a filename for a .pptx file"""