"""Student study tools: explanations, practice, revision aids, and image learning."""
from __future__ import annotations

import mimetypes
from pathlib import Path

from core import gemini


_MODES = {
    "explain": "Teach the topic step by step, starting with intuition, then key ideas and a worked example.",
    "flowchart": "Create a clear Mermaid flowchart for the topic. Return valid Mermaid syntax in a ```mermaid code block, followed by a short explanation of the flow.",
    "quiz": "Create a short interactive quiz. Ask one question at a time and wait for the student's answer. Do not reveal answers until asked.",
    "flashcards": "Create concise question-and-answer flashcards. Use numbered cards with a clear front and back.",
    "study_plan": "Create a realistic study plan with ordered sessions, time estimates, practice, and spaced review.",
    "practice": "Give a graduated set of practice problems from easy to challenging. Include hints first and solutions after a clearly marked answer key.",
    "summary": "Give a revision-focused summary with the essential concepts, definitions, and common misconceptions.",
    "analogy": "Teach the topic using an intuitive analogy, then connect each part of the analogy to the real concept and note where the analogy breaks down.",
    "image_explain": "Read the supplied image (such as a textbook page, diagram, or handwritten notes), explain its content, define important labels, and identify anything unclear rather than guessing.",
    "exam_review": "Make an exam-focused review guide: learning objectives, must-know facts, common traps, and a short self-check.",
}

_IMAGE_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
}
_MAX_IMAGE_BYTES = 15 * 1024 * 1024


def _image_part(image_path: str):
    path = Path(image_path).expanduser()
    if not path.is_file():
        raise ValueError(f"Image file not found: {image_path}")
    mime_type = _IMAGE_TYPES.get(path.suffix.lower())
    if not mime_type:
        guessed_type, _ = mimetypes.guess_type(str(path))
        if not guessed_type or not guessed_type.startswith("image/"):
            raise ValueError("Use a PNG, JPEG, WebP, GIF, or BMP image.")
        mime_type = guessed_type
    if path.stat().st_size > _MAX_IMAGE_BYTES:
        raise ValueError("Image is larger than the 15 MB study image limit.")

    from google.genai import types

    return types.Part.from_bytes(data=path.read_bytes(), mime_type=mime_type)


def study_tutor(parameters: dict, player=None) -> str:
    params = parameters or {}
    mode = str(params.get("mode", "explain")).strip().lower().replace("-", "_")
    if mode not in _MODES:
        return f"Unknown study mode '{mode}'. Choose one of: {', '.join(_MODES)}."

    topic = str(params.get("topic", "")).strip()
    question = str(params.get("question", "")).strip()
    image_path = str(params.get("image_path", "")).strip()
    if not topic and not question and not image_path:
        return "Please provide a topic, question, or image path to study."
    if mode == "image_explain" and not image_path:
        return "Image study needs an image_path to a local PNG, JPEG, WebP, GIF, or BMP file."

    level = str(params.get("level", "beginner")).strip() or "beginner"
    language = str(params.get("language", "same as the student's request")).strip()
    try:
        count = max(1, min(20, int(params.get("count", 5))))
    except (TypeError, ValueError):
        return "The count must be a whole number between 1 and 20."

    request = topic or question or "the material shown in the image"
    prompt = f"""You are JARVIS Study Tutor. Help a student genuinely understand and remember the material.
Study mode: {mode}
Task: {_MODES[mode]}
Topic or question: {request}
Student level: {level}
Response language: {language}
Requested question/card/problem count: {count}

Teaching guidelines:
- Explain unfamiliar terms in plain language and build from prerequisites.
- Use accurate examples and show the reasoning, not just conclusions.
- Adapt the depth to the student's level; do not invent facts or pretend to read unclear material.
- For a flowchart, return valid Mermaid flowchart syntax that can be pasted into a Mermaid renderer.
- Keep the response organized with useful headings and finish with one brief check-for-understanding question, except in quiz mode."""

    if question:
        prompt += f"\nStudent's specific question: {question}"
    if params.get("goal"):
        prompt += f"\nStudy goal or deadline: {str(params['goal']).strip()[:500]}"

    if player:
        player.write_log(f"[Study] Preparing {mode.replace('_', ' ')} for {request[:80]}...")

    try:
        contents = [prompt]
        if image_path:
            contents.insert(0, _image_part(image_path))
        response = gemini.call(contents, tier=gemini.SMART, timeout_ms=90_000)
        if response is None:
            return "Study tutor could not reach an available AI model. Please try again later."
        answer = (getattr(response, "text", None) or "").strip()
        if not answer:
            return "Study tutor received an empty response. Please try again with a more specific topic."
        return answer
    except (OSError, ValueError) as exc:
        return f"Could not prepare study material: {exc}"
    except Exception as exc:
        print(f"[Study] Tutor request failed: {exc}")
        return f"Study tutor failed: {exc}"


TOOL = {
    "name": "study_tutor",
    "description": (
        "Teach and coach students on a topic. Supports step-by-step explanations, "
        "Mermaid flowcharts, interactive quizzes, flashcards, practice problems, "
        "study plans, revision summaries, exam review, analogies, and explanations "
        "of textbook/diagram images supplied by local image_path."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "mode": {
                "type": "STRING",
                "description": "explain | flowchart | quiz | flashcards | study_plan | practice | summary | analogy | image_explain | exam_review",
            },
            "topic": {"type": "STRING", "description": "Topic or subject to learn"},
            "question": {"type": "STRING", "description": "Specific question from the student"},
            "level": {"type": "STRING", "description": "Learner level, such as beginner, high school, or university"},
            "language": {"type": "STRING", "description": "Language for the learning material"},
            "image_path": {"type": "STRING", "description": "Optional local path to a textbook page, notes, or diagram image"},
            "goal": {"type": "STRING", "description": "Optional study objective or exam deadline"},
            "count": {"type": "INTEGER", "description": "Number of quiz questions, flashcards, or problems (1-20; default 5)"},
        },
        "required": ["mode"],
    },
    "handler": study_tutor,
}
