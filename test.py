from dotenv import load_dotenv
import os
load_dotenv()


from powerpoint_generative_ai.ppt_generator import PowerPointGenerator

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

USER_TEXTS = [
"""create a six slide powerpoint about the growing obesity rate and its effect on health insurance premiums.

here is some data for a chart:
x axis: 2010, 2012, 2014, 2016, 2018, 2020, 2022, 2024
US: 5%, 10%, 15%, 20%, 25%, 30%, 35%, 40%
UK: 3%, 6%, 9%, 12%, 15%, 18%, 21%, 24%
RU: 2%, 4%, 6%, 8%, 10%, 12%, 14%, 16%
FR: 7%, 14%, 21%, 28%, 35%, 42%, 49%, 56%
IT: 1%, 2%, 3%, 4%, 5%, 6%, 7%, 8%


Also add a diagram about biology of fat cells. And a diagram about how sugar works.
""",
]


OUTLINE = [
    "Give a title to the presentation: Obesity and Health Insurance Premiums. Talk about how obesity effects health insurance premiums.",
    """Talk about how obesity is a growing problem in the US, UK, RU, FR, IT.
    here is some data for a chart:
    x axis: 2010, 2012, 2014, 2016, 2018, 2020, 2022, 2024
    US: 5%, 10%, 15%, 20%, 25%, 30%, 35%, 40%
    UK: 3%, 6%, 9%, 12%, 15%, 18%, 21%, 24%
    RU: 2%, 4%, 6%, 8%, 10%, 12%, 14%, 16%
    FR: 7%, 14%, 21%, 28%, 35%, 42%, 49%, 56%
    IT: 1%, 2%, 3%, 4%, 5%, 6%, 7%, 8%
    """,
    "Educate the user on the biology of fat cells. Add a diagram about biology of fat cells.",
    "Educate the user on how sugar works. Add a diagram about how sugar works.",
    "Talk about the problems caused by obesity.",
    "Provide an outro on the topic: Obesity and Health Insurance Premiums."
]

OUTLINE2 = [
    """
    Bar graph with 3 bars as depicted below
    Only need % and UCL plotted.
    Include dotted like at 34.4% “Performance Goal”
    UCL % should be included at top of UCL

    Total DRUG
N = 157

Proportion of patients with Event
15.9% 
(UCL 21.3%)
(LCL 11%)

========

DRUG Subgroup A
N = 41

2.4% 
(UCL 10.2%)
(LCL 0%)


========

DRUG Subgroup B
N = 116

20.7% 
(UCL 27.5%)
(LCL 0%)

    """,

    """
Title: Incidence of AE TERM Following Treatment with DRUGSub-title: National Health Reporting System in United States Between January 2021 – January 2022 [please make this look nice – not as important as main title – should be contained in title box though so searchable on iPad]

Create Horizontal bar graph showing number of events for top 3 age groups (exclude 30+)

Need to compare males vs females for each age category

X-axis = Incidence of AE TERM (per 1 Million Doses)

Please include placeholder footnote as client needs to include

Since comparisons are between sex within age groups – try to separate age groups with vertical backfill for some other nice element so separated visually

Data:
Age group,Males,Females
5 to 11,145,63
12 to 17,456,263
18 to 29,554,123
30+,572,326
""",

"""
Title: enrollment distribution by aneurysm size and rupture status (ITT)

Create two side-by-side bar graphs. (1-Left) unruptured (2-right) ruptured.

Plot %s on Y-Axis by Sac Width on X-axis. Note – you need to calculate %s which is =(x/N)*100

Y-axis scales should be the same on both plots and should be in-line (eg 10% should be same on both plots so message not skewed when comparing data on two figures)

Unruptured and ruptured bars should be different colors – not necessary to distinguish sac widths with different colors

Include N in legend

X-axis label = Aneurysm Sac Width (mm)

Data:

Extracted data from the table in the image in CSV format:

Sac width,N,x,n
>3-4,5,141,1
>4-5,29,141,9
>5-6,27,141,3
>6-7,32,141,1
>7-8,28,141,1
>8-9,13,141,-
>9-10,6,-,141
>10-11,-,>11-12,1
>11-12,1,141,-
""",

"""
Title: study 910: primary endpoint demonstrates meaningful activity in patients with severe disease

Create two stacked bar graphs showing ORR and CBR side by side and include the breakdown of responses within each – outlined below

ORR = Overall Response Rate [spell out below figure]

PR: partial response
VGPR: very good partial response
sCR: stringent complete response

Note: you will plot percentages

No need to label each piece of the stacked rather use color coded legend to distinguish response and number of patients.

Above this stack – put a text box with overall ORR % and (95% CI)


====

CBR = Clinical Benefit Rate [spell out below figure]

MR: minimal response 
PR: partial response
VGPR: very good partial response
sCR: stringent complete response

Note: you will plot percentages

No need to label each piece of the stacked rather use color coded legend to distinguish response and number of patients.

Above this stack – put a text box with overall CBR % and (95% CI)


======

CSV Data:

Category,ORR a,n (%)
KCP-330-012 mITT (N = 122),31 (25.4),18.0, 34.1
CBR b,n (%)
48 (39.3),30.6, 48.6
Best Response
sCR/CR,n (%)
2 (1.6),0.2, 5.8
GPR,n (%)
6 (4.9),1.8, 10.4
PR,n (%)
23 (18.9),12.3, 26.9
MR,n (%)
17 (13.9),8.3, 21.4
SD,n (%)
48 (39.3),30.6, 48.6
PD/NE,n (%)
26 (21.3),14.4, 29.6

"""
]


OUTLINE3 = [
    """
Title: baseline demographics were balanced between groups

Format table showing:
Age (years), mean (SD)
Female
While
Black or African American
Asian
Hispanic or Latino

All will be %’s except for age

Only show Drug / Placebo - Drug on left

CSV Data, generate a table:
Category,ORR a,n (%)
KCP-330-012 mITT (N = 122),31 (25.4),18.0, 34.1
CBR b,n (%)
48 (39.3),30.6, 48.6
Best Response
sCR/CR,n (%)
2 (1.6),0.2, 5.8
GPR,n (%)
6 (4.9),1.8, 10.4
PR,n (%)
23 (18.9),12.3, 26.9
MR,n (%)
17 (13.9),8.3, 21.4
SD,n (%)
48 (39.3),30.6, 48.6
PD/NE,n (%)
26 (21.3),14.4, 29.6

=========

Generate a table using the data above. Do not generate a graph.
""",
    """
    Title: resistance to multiple oral antibiotics further complicates treatment of cUTI in out-patient setting
Table should show:
Cefuroxime (β-lactam)
Ciprofloxacin (fluroquinolone)
Levofloxacin (fluroquinolone)
Trimethoprim-sulfamethoxazole

Overarching table header: “Co-Resistant Agent (Class)” [REF - Critchley, 2019]
Show on Right [Column 3]
Show on Left [Column 2]
Bullet at bottom: 1 in 8 patients with cUTI infected with pathogen resistant to ≥ 3 most common classes of antibiotics

CSV Data:
Agent,Trimethoprim-sulfamethoxazole (N=588),Levofloxacin (N=445)
Cefuroxime,31.3,45.7
Ceftazidime,15.0,24.7
Ciprofloxacin,44.2,100
Levofloxacin,42.5,100
Doripenem,0.0,0.0
Ertapenem,0.3,0.5
Imipenem,0.0,0.0
Meropenem,0.0,0.0
Trimethoprim-sulfamethoxazole,100,56.2

""",
"""
Bar graph with 3 bars as depicted below
    Only need % and UCL plotted.
    Include dotted like at 34.4% “Performance Goal”
    UCL % should be included at top of UCL

    Total DRUG
N = 157

Proportion of patients with Event
15.9% 
(UCL 21.3%)
(LCL 11%)

========

DRUG Subgroup A
N = 41

2.4% 
(UCL 10.2%)
(LCL 0%)


========

DRUG Subgroup B
N = 116

20.7% 
(UCL 27.5%)
(LCL 0%)


""",
"""
Title: Incidence of AE TERM Following Treatment with DRUGSub-title: National Health Reporting System in United States Between January 2021 – January 2022 [please make this look nice – not as important as main title – should be contained in title box though so searchable on iPad]

Create Horizontal bar graph showing number of events for top 3 age groups (exclude 30+)

Need to compare males vs females for each age category

X-axis = Incidence of AE TERM (per 1 Million Doses)

Please include placeholder footnote as client needs to include

Since comparisons are between sex within age groups – try to separate age groups with vertical backfill for some other nice element so separated visually

Data:
Age group,Males,Females
5 to 11,145,63
12 to 17,456,263
18 to 29,554,123
30+,572,326
""",
"""
Title: enrollment distribution by aneurysm size and rupture status (ITT)

Create two side-by-side bar graphs. (1-Left) unruptured (2-right) ruptured.

Plot %s on Y-Axis by Sac Width on X-axis. Note – you need to calculate %s which is =(x/N)*100

Y-axis scales should be the same on both plots and should be in-line (eg 10% should be same on both plots so message not skewed when comparing data on two figures)

Unruptured and ruptured bars should be different colors – not necessary to distinguish sac widths with different colors

Include N in legend

X-axis label = Aneurysm Sac Width (mm)

Data:

Extracted data from the table in the image in CSV format:

Sac width,N,x,n
>3-4,5,141,1
>4-5,29,141,9
>5-6,27,141,3
>6-7,32,141,1
>7-8,28,141,1
>8-9,13,141,-
>9-10,6,-,141
>10-11,-,>11-12,1
>11-12,1,141,-
""",
"""
Title: study 910: primary endpoint demonstrates meaningful activity in patients with severe disease

Create two stacked bar graphs showing ORR and CBR side by side and include the breakdown of responses within each – outlined below

ORR = Overall Response Rate [spell out below figure]

PR: partial response
VGPR: very good partial response
sCR: stringent complete response

Note: you will plot percentages

No need to label each piece of the stacked rather use color coded legend to distinguish response and number of patients.

Above this stack – put a text box with overall ORR % and (95% CI)


====

CBR = Clinical Benefit Rate [spell out below figure]

MR: minimal response 
PR: partial response
VGPR: very good partial response
sCR: stringent complete response

Note: you will plot percentages

No need to label each piece of the stacked rather use color coded legend to distinguish response and number of patients.

Above this stack – put a text box with overall CBR % and (95% CI)


======

CSV Data:

Category,ORR a,n (%)
KCP-330-012 mITT (N = 122),31 (25.4),18.0, 34.1
CBR b,n (%)
48 (39.3),30.6, 48.6
Best Response
sCR/CR,n (%)
2 (1.6),0.2, 5.8
GPR,n (%)
6 (4.9),1.8, 10.4
PR,n (%)
23 (18.9),12.3, 26.9
MR,n (%)
17 (13.9),8.3, 21.4
SD,n (%)
48 (39.3),30.6, 48.6
PD/NE,n (%)
26 (21.3),14.4, 29.6

"""


]


def generate_ppt():
    ppt_generator = PowerPointGenerator(OPENAI_API_KEY)
    powerpoint_files = [ppt_generator.create_powerpoint(user_input=user_text) for user_text in USER_TEXTS]
    
def generate_ppt_from_outline():
    ppt_generator = PowerPointGenerator(OPENAI_API_KEY)
    powerpoint_files = ppt_generator.create_powerpoint_from_outline(outline=[OUTLINE3[0]])
    print(powerpoint_files)

if __name__ == "__main__":
    # generate_ppt()
    generate_ppt_from_outline()