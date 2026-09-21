from typing import TypedDict

from langgraph.graph import (
    StateGraph,
    START,
    END,
)

from app.ai.rag import (
    retrieve_chapter,
    context_from_chunks,
)

from app.ai.service import (
    extract_concepts,
    generate_lesson,
    generate_questions,
)


class LessonState(TypedDict, total=False):

    chapter_id: str

    topic: str

    age: int

    number_of_questions: int

    db: object

    context: str

    concepts: dict

    lesson: dict

    questions: dict


async def retrieve_node(state):

    chunks = await retrieve_chapter(
        state["db"],
        state["chapter_id"],
    )

    if not chunks:
        raise ValueError(
            "No chapter content was found."
        )

    context = context_from_chunks(
        chunks
    )

    return {
        "context": context
    }


def concepts_node(state):

    return {
        "concepts": extract_concepts(
            state["context"]
        )
    }


def lesson_node(state):

    return {
        "lesson": generate_lesson(
            state["context"],
            state["concepts"],
            state["age"],
        )
    }


def questions_node(state):

    return {
        "questions": generate_questions(
            state["context"],
            state["lesson"],
            state["age"],
            state[
                "number_of_questions"
            ],
        )
    }


def build_graph():

    g = StateGraph(
        LessonState
    )

    g.add_node(
        "retrieve",
        retrieve_node,
    )

    g.add_node(
        "concepts",
        concepts_node,
    )

    g.add_node(
        "lesson",
        lesson_node,
    )

    g.add_node(
        "questions",
        questions_node,
    )

    g.add_edge(
        START,
        "retrieve",
    )

    g.add_edge(
        "retrieve",
        "concepts",
    )

    g.add_edge(
        "concepts",
        "lesson",
    )

    g.add_edge(
        "lesson",
        "questions",
    )

    g.add_edge(
        "questions",
        END,
    )

    return g.compile()