import json

from app.ai.models import llm_provider
from app.ai.prompts import (
    CONCEPT_PROMPT,
    LESSON_PROMPT,
    QUESTION_PROMPT,
    EVAL_PROMPT,
    CHAPTER_FROM_TEXT_PROMPT,
)


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

def extract_concepts(context):

    prompt = CONCEPT_PROMPT.replace(
        "{context}",
        context,
    )

    response = llm_provider.chat(prompt)

    return _json(response.content)


def generate_lesson(context, concepts, age):

    prompt = (
        LESSON_PROMPT
        .replace("{context}", context)
        .replace(
            "{concepts}",
            json.dumps(concepts),
        )
        .replace(
            "{age}",
            str(age),
        )
    )

    response = llm_provider.chat(prompt)

    return _json(response.content)


def generate_questions(
    context,
    lesson,
    age,
    n,
):

    prompt = (
        QUESTION_PROMPT
        .replace("{context}", context)
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