OWNER = "Anuj Joshi"

# ── Portfolio Agent ────────────────────────────────────────────────────────────
PORTFOLIO_FOLLOWUP_PROMPT = f"""
# Role: Predictive user-intent engine for a personal portfolio chatbot.
# Task: Generate 3-5 short follow-up questions (max 6 words each) that a recruiter or hiring manager would naturally ask after the previous response about {OWNER}'s background, skills, projects, or experience.
# Focus on: background, technical skills, work experience, projects, contact info.
# Constraint: Only suggest questions that can be answered from the portfolio (education, experience, skills, projects, contact). Do not suggest questions that would require invented or unverifiable facts.
""".strip()

PORTFOLIO_DEFAULT_FOLLOWUPS = [
    "Tell me about Anuj's background",
    "What are Anuj's key technical skills?",
    "Show me some of Anuj's featured projects",
    "What is Anuj's work experience?",
    "How can I contact Anuj?",
]

# ── Open-Source Agent ──────────────────────────────────────────────────────────
OPEN_SOURCE_FOLLOWUP_PROMPT = f"""
# Role: Predictive user-intent engine for a GitHub open-source assistant.
# Task: Generate 3-5 short follow-up questions (max 6 words each) that a developer or recruiter would naturally ask after the previous response about {OWNER}'s GitHub repositories, contributions, pull requests, or open-source activity.
# Focus on: repositories, recent commits, stars, languages, PRs, issues, contribution streaks.
# Constraint: Only suggest questions that can be answered from GitHub tool data (repos, commits, stars, languages, etc.). Do not suggest questions that would require made-up repos, stats, or facts.
""".strip()

OPEN_SOURCE_DEFAULT_FOLLOWUPS = [
    "List anujjoshi3105's top repositories",
    "Show recent GitHub activity",
    "Tell me about his pull requests",
    "Show contributions in the last month",
    "What languages does Anuj use most?",
]

# ── Competitive Programming Agent ──────────────────────────────────────────────
CP_FOLLOWUP_PROMPT = f"""
# Role: Predictive user-intent engine for a competitive programming stats assistant.
# Task: Generate 3-5 short follow-up questions (max 6 words each) that a developer or recruiter would naturally ask after the previous response about {OWNER}'s contest ratings, problem-solving stats, or platform rankings.
# Focus on: LeetCode, Codeforces, AtCoder, CodeChef, contest history, problem counts, rankings.
# Constraint: Only suggest questions that can be answered from CP platform/tool data (ratings, problems solved, rankings). Do not suggest questions that would require invented stats or platforms.
""".strip()

CP_DEFAULT_FOLLOWUPS = [
    "Show Anuj's LeetCode rating and stats",
    "What is Anuj's Codeforces rank?",
    "Get recent contest performance",
    "Show CP stats across all platforms",
    "How many problems has Anuj solved?",
]

# ── Lookup maps (used by FollowUpMiddleware) ───────────────────────────────────
FOLLOWUP_PROMPTS: dict[str, str] = {
    "portfolio-agent": PORTFOLIO_FOLLOWUP_PROMPT,
    "open-source-agent": OPEN_SOURCE_FOLLOWUP_PROMPT,
    "competitive-programming-agent": CP_FOLLOWUP_PROMPT,
}

DEFAULT_FOLLOWUP_PROMPTS_MAP: dict[str, list[str]] = {
    "portfolio-agent": PORTFOLIO_DEFAULT_FOLLOWUPS,
    "open-source-agent": OPEN_SOURCE_DEFAULT_FOLLOWUPS,
    "competitive-programming-agent": CP_DEFAULT_FOLLOWUPS,
}

# ── Backwards-compat aliases ───────────────────────────────────────────────────
FOLLOWUP_GENERATION_PROMPT = PORTFOLIO_FOLLOWUP_PROMPT
DEFAULT_FOLLOWUP_PROMPTS = PORTFOLIO_DEFAULT_FOLLOWUPS
