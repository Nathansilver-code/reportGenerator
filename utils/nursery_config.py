"""
Settings for the nursery section.
Edit THIS file to rename classes, change colours, or add/remove report items.
(Report items live in the database as JSON, so changing them needs no migration.)
"""

SCHOOL_NAME    = "MARANATHA NURSERY SCHOOL - WAMPEEWO"
SCHOOL_ADDRESS = "Located 8 miles off Kampala-Gayaza Road, Magere - Kito Village"
SCHOOL_CONTACT = "P.O Box 153490, Kampala   |   Tel: 0702-619008 / 0787-908562"

NURSERY_CLASSES = ["ECD ONE", "ECD TWO", "ECD THREE"]
TERMS           = ["Term 1", "Term 2", "Term 3"]

REPORT_TYPES    = ["End of Term", "Mid Term"]

# Printed on EVERY nursery card (not typed in per learner).
# Change these here when they change - for example the date every new term.
NEXT_TERM_BEGINS = "14th September 2026"
FEES_DAY         = "Refer to requirement sheet"
FEES_BOARDERS    = "650,000/="

# Writing size. 1.0 = the first design; every size on the card grows by the same factor.
PDF_MAX_FONT_SCALE = 1.35     # the PDF uses the biggest size (up to this) that still fits one page
SCREEN_FONT_SCALE  = 1.25     # card shown on the screen
PRINT_FONT_SCALE   = 1.2      # browser Print button (one A4 page)

# Optional picture faintly behind the card: save it as static/img/nursery/background.jpg
# (or .png / .jpeg / .webp). No file = no background. Higher number = stronger picture.
BACKGROUND_STRENGTH = 0.12

# Best to weakest, in the order shown on the card's grading bar
GRADE_LEVELS = [
    {"name": "Outstanding",  "color": "#d62828", "text": "#ffffff"},
    {"name": "Very Good",    "color": "#2f6fdb", "text": "#ffffff"},
    {"name": "Good",         "color": "#f7d917", "text": "#1f2937"},
    {"name": "Satisfactory", "color": "#5e2a9c", "text": "#ffffff"},
    {"name": "Fair",         "color": "#43a047", "text": "#ffffff"},
]
GRADE_NAMES = [g["name"] for g in GRADE_LEVELS]
GRADE_MAP   = {g["name"]: g for g in GRADE_LEVELS}

SKILLS = [
    ("learning_dev_one", "Learning development one"),
    ("math_concepts",    "Mathematical concepts"),
    ("social_dev",       "Social development"),
    ("learning_dev_two", "Learning development two"),
    ("health_habits",    "Health habits"),
]

TRAITS = [
    ("friendly",   "Friendly and courteous"),
    ("punctual",   "Punctual"),
    ("clean",      "Clean and orderly"),
    ("attentive",  "Attentive"),
    ("respectful", "Respectful"),
]

ALL_ITEMS = SKILLS + TRAITS


def report_title(report_type):
    return f"{report_type.upper()} CLASS REPORT"