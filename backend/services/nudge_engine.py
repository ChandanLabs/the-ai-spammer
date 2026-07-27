"""
nudge_engine.py — AI message generation with 3 escalation levels
Level 1 (nudge_count 0-1): Polite reminder
Level 2 (nudge_count 2-4): Urgent reminder
Level 3 (nudge_count 5+):  FOMO message
"""
import logging
from datetime import datetime
from typing import Optional

from backend.config import settings

logger = logging.getLogger(__name__)


def get_nudge_level(nudge_count: int) -> int:
    if nudge_count <= 1:
        return 1
    elif nudge_count <= 4:
        return 2
    else:
        return 3


def _fallback_message(name: str, company: str, deadline_str: str, level: int) -> str:
    if level == 1:
        return (
            f"Hi {name}! 👋 Just a friendly reminder that you haven't registered for "
            f"*{company}* yet.\n\n⏰ Deadline: *{deadline_str}*\n\nDon't miss out! Reply /status to check your status."
        )
    elif level == 2:
        return (
            f"⚠️ *Urgent Reminder, {name}!*\n\n"
            f"The deadline for *{company}* is approaching fast: *{deadline_str}*\n\n"
            f"You are still NOT registered. Please act NOW before it's too late! 🏃‍♂️\n\n"
            f"Reply /status to verify your status."
        )
    else:
        return (
            f"🚨 *Last Chance, {name}!*\n\n"
            f"Most of your peers have already registered for *{company}*. "
            f"Are you really going to miss this opportunity?\n\n"
            f"Deadline: *{deadline_str}* — time is running out! ⏳\n\n"
            f"Reply /status to check your status."
        )


async def generate_nudge_message(
    name: str,
    roll_number: str,
    company_name: str,
    deadline: datetime,
    nudge_count: int,
) -> str:
    level = get_nudge_level(nudge_count)
    deadline_str = deadline.strftime("%d %B %Y at %I:%M %p")
    hours_left = max(0, int((deadline - datetime.utcnow()).total_seconds() / 3600))

    try:
        if settings.AI_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
            return await _gemini_message(name, company_name, deadline_str, hours_left, level)
        elif settings.AI_PROVIDER == "openai" and settings.OPENAI_API_KEY:
            return await _openai_message(name, company_name, deadline_str, hours_left, level)
    except Exception as e:
        logger.warning(f"AI generation failed (level {level}): {e} — using fallback")

    return _fallback_message(name, company_name, deadline_str, level)


LEVEL_PROMPTS = {
    1: "Write a polite, friendly reminder. Tone: warm and encouraging. Do NOT be alarming.",
    2: "Write an urgent reminder. Tone: concerned, firm. Emphasize the approaching deadline. Use urgency.",
    3: "Write a FOMO (Fear Of Missing Out) message. Mention that many peers have already registered. Tone: slightly dramatic but not rude.",
}


async def _gemini_message(
    name: str, company: str, deadline_str: str, hours_left: int, level: int
) -> str:
    import google.generativeai as genai
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = f"""You are a placement coordinator sending a Telegram message to a student.

Student Name: {name}
Company/Drive: {company}
Registration Deadline: {deadline_str} ({hours_left} hours remaining)
Status: NOT REGISTERED
Message Level: {level} — {LEVEL_PROMPTS[level]}

Write a Telegram message (max 120 words):
- Address the student by first name
- Mention the company and deadline clearly
- End with: "Reply /status to check your status."
- Use 1-2 relevant emojis naturally
- Use *bold* only for deadline and company name
- Output ONLY the message text"""

    resp = model.generate_content(prompt)
    return resp.text.strip()


async def _openai_message(
    name: str, company: str, deadline_str: str, hours_left: int, level: int
) -> str:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a placement coordinator sending Telegram reminders."},
            {"role": "user", "content": (
                f"Student: {name}, Company: {company}, Deadline: {deadline_str} ({hours_left}h left)\n"
                f"Level {level}: {LEVEL_PROMPTS[level]}\n"
                f"Max 120 words. End with 'Reply /status to check your status.' Output ONLY the message."
            )},
        ],
        max_tokens=200,
        temperature=0.85,
    )
    return resp.choices[0].message.content.strip()
