import json
import re

from app.ai.models import llm_provider
from app.ai.prompts import (
    CONCEPT_PROMPT,
    LESSON_PROMPT,
    QUESTION_PROMPT,
    EVAL_PROMPT,
    CHAPTER_FROM_TEXT_PROMPT,
)


def resolve_question_count(
    default_count: int,
    custom_prompt: str | None,
) -> int:

    if not custom_prompt:
        return default_count

    text = custom_prompt.lower()

    patterns = [
        r"\b(\d+)\s*(?:questions|question|mcqs|mcq)\b",
        r"\b(?:make|create|generate|give)\s+(\d+)\s+"
        r"(?:questions|question|mcqs|mcq)\b",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
        )

        if match:

            requested = int(
                match.group(1)
            )

            return max(
                1,
                min(requested, 20),
            )

    return default_count

def _json(text: str):
    text = text.strip()

    if text.startswith("```"):
        text = text.strip("`")

        if text.startswith("json"):
            text = text[4:]

    start = text.find("{")
    end = text.rfind("}")

    if start < 0 or end < 0:
        raise ValueError("AI did not return JSON")

    return json.loads(text[start:end + 1])

def generate_chapter_from_text(
    input_text,
    grade,
    language="English",
):
    prompt = (
        CHAPTER_FROM_TEXT_PROMPT
        .replace(
            "{input_text}",
            input_text,
        )
        .replace(
            "{grade}",
            str(grade),
        )
        .replace(
            "{language}",
            str(language),
        )
    )

    response = llm_provider.chat(prompt)

    return _json(response.content)

def extract_concepts(
    context,
    custom_prompt="",
):

    prompt = (
        CONCEPT_PROMPT
        .replace(
            "{context}",
            context,
        )
        .replace(
            "{custom_prompt}",
            custom_prompt or "No additional parent instructions.",
        )
    )

    response = llm_provider.chat(prompt)

    return _json(response.content)


def generate_lesson(
    context,
    concepts,
    age,
    custom_prompt="",
):

    prompt = (
        LESSON_PROMPT
        .replace(
            "{context}",
            context,
        )
        .replace(
            "{concepts}",
            json.dumps(concepts),
        )
        .replace(
            "{age}",
            str(age),
        )
        .replace(
            "{custom_prompt}",
            custom_prompt or "No additional parent instructions.",
        )
    )

    response = llm_provider.chat(prompt)

    return _json(response.content)


def generate_questions(
    context,
    lesson,
    age,
    n,
    custom_prompt="",
):

    prompt = (
        QUESTION_PROMPT
        .replace(
            "{context}",
            context,
        )
        .replace(
            "{lesson}",
            json.dumps(lesson),
        )
        .replace(
            "{age}",
            str(age),
        )
        .replace(
            "{n}",
            str(n),
        )
        .replace(
            "{custom_prompt}",
            custom_prompt or "No additional parent instructions.",
        )
    )

    response = llm_provider.chat(prompt)

    return _json(response.content)


def evaluate_answer(
    question,
    expected,
    answer,
):

    prompt = (
        EVAL_PROMPT
        .replace("{question}", question)
        .replace("{expected}", expected)
        .replace("{answer}", answer)
    )

    response = llm_provider.chat(prompt)

    return _json(response.content)