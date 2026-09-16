# test_questions.py
# Test cases based on Lakshay Agarwal's actual resume

TEST_CASES = [

    # ── EDUCATION ─────────────────────────────────────────────
    {
        "question": "What is the CGPA?",
        "expected_keywords": ["8.9", "cgpa"],
        "category": "education"
    },
    {
        "question": "Where did this person study for their engineering degree?",
        "expected_keywords": ["maharaja", "surajmal", "msit"],
        "category": "education"
    },
    {
        "question": "What year did this person graduate?",
        "expected_keywords": ["2025"],
        "category": "education"
    },
    {
        "question": "What was the grade in class 12th?",
        "expected_keywords": ["94", "94%", "grade"],
        "category": "education"
    },
    {
        "question": "Which school did this person attend for 12th?",
        "expected_keywords": ["delhi", "public", "school", "rohini", "dps"],
        "category": "education"
    },

    # ── SKILLS ────────────────────────────────────────────────
    {
        "question": "What programming languages does this person know?",
        "expected_keywords": ["c++", "java", "python"],
        "category": "skills"
    },
    {
        "question": "What web technologies does this person know?",
        "expected_keywords": ["node", "react", "express", "mongodb", "javascript"],
        "category": "skills"
    },
    {
        "question": "What databases has this person worked with?",
        "expected_keywords": ["mongodb", "mysql"],
        "category": "skills"
    },
    {
        "question": "Does this person know React?",
        "expected_keywords": ["react"],
        "category": "skills"
    },
    {
        "question": "Does this person know Python?",
        "expected_keywords": ["python"],
        "category": "skills"
    },

    # ── PROJECTS ──────────────────────────────────────────────
    {
        "question": "What projects has this person built?",
        "expected_keywords": ["music", "thoughtvine", "moviezone"],
        "category": "projects"
    },
    {
        "question": "Tell me about the music player project",
        "expected_keywords": ["react", "music", "restful", "api", "frontend"],
        "category": "projects"
    },
    {
        "question": "What is ThoughtVine?",
        "expected_keywords": ["blog", "express", "mongodb", "authentication", "crud"],
        "category": "projects"
    },
    {
        "question": "Tell me about the movie recommendation project",
        "expected_keywords": ["movie", "recommendation", "machine learning", "filtering"],
        "category": "projects"
    },
    {
        "question": "Which project used machine learning?",
        "expected_keywords": ["moviezone", "movie", "recommendation", "machine learning"],
        "category": "projects"
    },
    {
        "question": "What tech stack was used in ThoughtVine?",
        "expected_keywords": ["express", "mongodb", "node", "passport", "handlebars"],
        "category": "projects"
    },

    # ── ACHIEVEMENTS ──────────────────────────────────────────
    {
        "question": "What achievements does this person have?",
        "expected_keywords": ["hackathon", "code4cause", "top 10", "2000"],
        "category": "achievements"
    },
    {
        "question": "What hackathon did this person participate in?",
        "expected_keywords": ["code4cause", "hack", "top 10", "2000"],
        "category": "achievements"
    },

    # ── CERTIFICATIONS ────────────────────────────────────────
    {
        "question": "What certifications does this person have?",
        "expected_keywords": ["data structures", "algorithms", "mern", "udemy"],
        "category": "certifications"
    },
    {
        "question": "Where did this person get their DSA certification?",
        "expected_keywords": ["udemy"],
        "category": "certifications"
    },

    # ── CONTACT ───────────────────────────────────────────────
    {
        "question": "What is the email address?",
        "expected_keywords": ["lakshayagarwal365", "gmail"],
        "category": "contact"
    },
    {
        "question": "What is the phone number?",
        "expected_keywords": ["9873881187"],
        "category": "contact"
    },

    # ── MEMORY TEST QUESTIONS (asked in sequence) ─────────────
    {
        "question": "What is the most complex project this person has built?",
        "expected_keywords": ["moviezone", "movie", "machine learning"],
        "category": "analysis"
    },
    {
        "question": "Is this person a frontend or backend developer?",
        "expected_keywords": ["react", "node", "express", "full", "frontend", "backend"],
        "category": "analysis"
    },
    {
        "question": "Would this person be a good fit for a MERN stack role?",
        "expected_keywords": ["mongodb", "express", "react", "node", "mern"],
        "category": "analysis"
    },
]