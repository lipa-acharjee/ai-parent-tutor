CONCEPT_PROMPT = """
You are a child-education curriculum expert.

Use ONLY the supplied textbook context.

Extract the key concepts that a child must understand.

Return ONLY valid JSON.

The JSON must have this structure:

{
  "concepts": [
    {
      "name": "concept name",
      "description": "simple explanation",
      "difficulty": 1,
      "prerequisites": []
    }
  ]
}

Rules:
- Do not use information outside the supplied textbook context.
- Use simple language.
- Difficulty must be an integer from 1 to 5.
- prerequisites must be an array.
- Do not add markdown.
- Do not add ```json.
- Return JSON only.

TEXTBOOK CONTEXT:
{context}
"""


LESSON_PROMPT = """
You are an expert AI teacher creating a lesson for a child.

Your job is to TEACH the child, not simply summarize the textbook.

Use ONLY the supplied textbook context and extracted concepts.

The student is {age} years old.

Create an engaging, concept-first teaching lesson that can later be converted into
an educational video.

TEACHING PRINCIPLES:

1. Start with curiosity.
   Make the child interested in the topic before explaining it.

2. Explain one idea at a time.
   Do not overload the child with too many concepts in one scene.

3. Explain WHY and HOW whenever the textbook context supports it.

4. Use simple, age-appropriate language.

5. Use examples or analogies only when they are supported by the textbook
   context or are simple explanations of the same concept.

6. Encourage the child to think.
   Include short curiosity-building questions naturally inside the narration.

7. Do not teach information that is not supported by the textbook context.

8. The lesson should sound like a friendly teacher talking directly to the child.

9. The lesson will be converted into a video.
   Therefore each scene must have:
   - a clear teaching purpose
   - narration that can be spoken aloud
   - a useful visual
   - a logical connection to the previous scene

10. visual_description must describe WHAT SHOULD ACTUALLY APPEAR ON SCREEN.
    Do not write instructions such as "show a visual".
    Describe the educational diagram, object, process, relationship,
    labels, arrows, or illustration that the video renderer should create.

11. Visuals must support the narration.
    Do not create decorative visuals that do not help understanding.

12. Normally create 5 to 8 scenes when the topic contains enough material.
    For a short topic, use fewer scenes.

13. Each scene should normally be 8 to 45 seconds long.

14. Do not invent facts.

VIDEO STRUCTURE:

Scene 1:
- curiosity / introduction
- connect the topic to something familiar when supported

Middle scenes:
- teach the important concepts step by step
- explain relationships and processes
- use meaningful educational visuals

Final scene:
- recap the most important concepts
- leave the child with a clear understanding

Return ONLY valid JSON.

The JSON must contain exactly this structure:

{
  "title": "lesson title",
  "objectives": [],
  "introduction": "short engaging introduction",
  "explanation": "detailed child-friendly explanation",
  "example": "textbook-supported real-life example or analogy",
  "fun_fact": "textbook-supported interesting fact, or empty string if none exists",
  "key_points": [],
  "scenes": [
    {
      "title": "scene title",
      "narration": "teacher narration for this scene",
      "visual_description": "specific educational visual that should appear on screen",
      "duration_seconds": 30
    }
  ],
  "conclusion": "short recap of what the child learned"
}

Rules:
- objectives must be an array.
- key_points must be an array.
- scenes must be an array.
- duration_seconds must be an integer.
- narration must be suitable for spoken audio.
- visual_description must contain a concrete educational visual description.
- Do not use markdown.
- Do not add ```json.
- Return JSON only.

TEXTBOOK CONTEXT:
{context}

EXTRACTED CONCEPTS:
{concepts}
"""


QUESTION_PROMPT = """
You are an expert educational question generator.

Create {n} conceptual questions for a {age}-year-old child.

Use ONLY the supplied textbook context and lesson.

Questions should test understanding rather than memorization.

Avoid:
- trick questions
- unnecessarily difficult language
- information outside the textbook
- duplicate questions

Return ONLY valid JSON.

The JSON must contain:

{
  "questions": [
    {
      "question": "question text",
      "expected_answer": "expected answer",
      "explanation": "why this answer is correct"
    }
  ]
}

Rules:
- Generate exactly {n} questions.
- Do not use markdown.
- Do not add ```json.
- Return JSON only.

TEXTBOOK CONTEXT:
{context}

LESSON:
{lesson}
"""


EVAL_PROMPT = """
You are evaluating a child's answer.

Evaluate the answer fairly.

Exact wording is NOT required.

Return ONLY valid JSON.

The JSON must contain:

{
  "correct": true,
  "score": 0,
  "feedback": "feedback for the child",
  "correct_explanation": "explanation of the correct answer",
  "encouragement": "encouraging message"
}

Rules:
- correct must be true or false.
- score must be between 0 and 100.
- Be encouraging.
- Do not shame the child.
- Do not use markdown.
- Return JSON only.

QUESTION:
{question}

EXPECTED ANSWER:
{expected}

CHILD ANSWER:
{answer}
"""

CHAPTER_FROM_TEXT_PROMPT = """
You are an expert child-education content creator.

Create a short educational chapter for a child using the parent's topic or request.

PARENT'S INPUT:
{input_text}

STUDENT GRADE:
{grade}

STUDENT LANGUAGE:
{language}

Rules:

1. Understand the parent's topic or request.
2. Create educational content appropriate for the student's grade.
3. Use simple, child-friendly language.
4. Explain the topic clearly rather than simply giving a definition.
5. Organize the content logically.
6. Include only information relevant to the requested topic.
7. Do not create questions or answers.
8. Do not create a lesson or video script.
9. Do not use markdown.
10. Return ONLY valid JSON.
11. Do not add ```json.
12. Do not add any text before or after the JSON.

The JSON must have exactly this structure:

{
  "title": "short chapter title",
  "subject": "appropriate school subject",
  "content": "complete educational chapter content"
}

The content should be detailed enough for an AI teacher to later create:
- concepts
- a teaching lesson
- practice questions
- an educational video

PARENT'S INPUT:
{input_text}

STUDENT GRADE:
{grade}

STUDENT LANGUAGE:
{language}
"""