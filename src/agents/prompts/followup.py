DEFAULT_FOLLOWUP_PROMPTS = [
    "Tell me about Anuj's background",
    "What are Anuj's key technical skills?",
    "Show me some of Anuj's featured projects",
    "What is Anuj's work experience?",
    "How can I contact Anuj?",
]

FOLLOWUP_GENERATION_PROMPT = f"""
# Role: You are a predictive user intent engine.
# Task: Generate 3-5 suggested follow-up options that the USER would click to ask the chatbot. Based on the previous message, predict the most logical next steps for the user.
"""
