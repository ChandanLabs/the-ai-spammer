import logging
from datetime import datetime
from typing import Optional
from ..config import settings
from ..models import Student, Campaign

logger = logging.getLogger(__name__)


async def generate_nudge_message(
    student: Student,
    campaign: Campaign,
    template: Optional[str] = None,
) -> str:
    """
    Generate a personalized nudge message using Gemini or OpenAI.
    Falls back to template or default message if AI is disabled or fails.
    """
    if not campaign.use_ai:
        return _render_template(template or campaign.message_template, student, campaign)

    try:
        if settings.AI_PROVIDER == "gemini":
            return await _generate_gemini(student, campaign)
        elif settings.AI_PROVIDER == "openai":
            return await _generate_openai(student, campaign)
    except Exception as e:
        logger.error(f"AI generation failed: {e}. Falling back to template.")

    return _render_template(campaign.message_template, student, campaign)


def _render_template(template: Optional[str], student: Student, campaign: Campaign) -> str:
    """Render a message template with student and campaign placeholders."""
    deadline_str = campaign.deadline.strftime("%d %B %Y, %I:%M %p")
    default = (
        f"Hi {student.name}! 👋\n\n"
        f"This is a reminder that you haven't completed your placement registration "
        f"for *{campaign.name}*.\n\n"
        f"⏰ Deadline: *{deadline_str}*\n\n"
        f"Please register ASAP to avoid missing out. "
        f"Reply /status to check your current status."
    )
    if not template:
        return default
    return (
        template
        .replace("{name}", student.name)
        .replace("{roll_no}", student.roll_no)
        .replace("{campaign}", campaign.name)
        .replace("{deadline}", deadline_str)
        .replace("{email}", student.email)
    )


async def _generate_gemini(student: Student, campaign: Campaign) -> str:
    import google.generativeai as genai

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

    deadline_str = campaign.deadline.strftime("%d %B %Y at %I:%M %p")
    hours_left = max(0, int((campaign.deadline - datetime.utcnow()).total_seconds() / 3600))

    prompt = f"""You are a friendly placement coordinator sending a Telegram reminder to a student.

Student Name: {student.name}
Roll Number: {student.roll_no}
Campaign: {campaign.name}
Deadline: {deadline_str} ({hours_left} hours remaining)
Status: NOT YET REGISTERED

Write a short, warm, urgent but friendly Telegram reminder message (max 150 words).
- Use the student's first name
- Mention the deadline clearly
- Add urgency without being harsh
- Use 1-2 relevant emojis naturally
- End with: "Reply /status to check your status."
- Use plain text, no markdown except for **bold** on the deadline
- Keep it conversational, not robotic

Output ONLY the message text, nothing else."""

    response = model.generate_content(prompt)
    return response.text.strip()


async def _generate_openai(student: Student, campaign: Campaign) -> str:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    deadline_str = campaign.deadline.strftime("%d %B %Y at %I:%M %p")
    hours_left = max(0, int((campaign.deadline - datetime.utcnow()).total_seconds() / 3600))

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a friendly placement coordinator sending Telegram reminders.",
            },
            {
                "role": "user",
                "content": (
                    f"Write a short (max 150 words) warm but urgent Telegram reminder for:\n"
                    f"Student: {student.name} (Roll: {student.roll_no})\n"
                    f"Campaign: {campaign.name}\n"
                    f"Deadline: {deadline_str} ({hours_left} hours left)\n"
                    f"They have NOT registered yet.\n"
                    f"End with: 'Reply /status to check your status.'\n"
                    f"Output ONLY the message text."
                ),
            },
        ],
        max_tokens=200,
        temperature=0.8,
    )
    return response.choices[0].message.content.strip()
