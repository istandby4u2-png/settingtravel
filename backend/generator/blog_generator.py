import json
import os
import re
from google import genai
from google.genai import types


def _build_style_prompt(style_profile: dict) -> str:
    """Build a system prompt from the style analysis profile."""
    stats = style_profile.get("statistical", {})
    ai = style_profile.get("ai_analysis", {})

    parts = ["당신은 특정 블로거의 문체를 완벽하게 모방하는 글쓰기 전문가입니다.\n"]
    parts.append("아래는 해당 블로거의 문체 분석 결과입니다. 이 스타일을 정확히 따라주세요.\n")

    if ai:
        if ai.get("overall_tone"):
            parts.append(f"- 전체 톤: {ai['overall_tone']}")
        if ai.get("writing_persona"):
            parts.append(f"- 페르소나: {ai['writing_persona']}")
        if ai.get("narrative_style"):
            parts.append(f"- 서술 방식: {ai['narrative_style']}")
        if ai.get("vocabulary_level"):
            parts.append(f"- 어휘 수준: {ai['vocabulary_level']}")
        if ai.get("sentence_structure"):
            parts.append(f"- 문장 구조: {ai['sentence_structure']}")
        if ai.get("paragraph_organization"):
            parts.append(f"- 문단 구성: {ai['paragraph_organization']}")
        if ai.get("rhetorical_devices"):
            devices = ", ".join(ai["rhetorical_devices"]) if isinstance(ai["rhetorical_devices"], list) else ai["rhetorical_devices"]
            parts.append(f"- 수사법: {devices}")
        if ai.get("emotional_expression"):
            parts.append(f"- 감정 표현: {ai['emotional_expression']}")
        if ai.get("opening_pattern"):
            parts.append(f"- 글 시작 패턴: {ai['opening_pattern']}")
        if ai.get("closing_pattern"):
            parts.append(f"- 글 마무리 패턴: {ai['closing_pattern']}")
        if ai.get("unique_characteristics"):
            chars = ai["unique_characteristics"]
            if isinstance(chars, list):
                parts.append(f"- 독특한 특징: {', '.join(chars)}")
        if ai.get("reader_engagement"):
            parts.append(f"- 독자 소통 방식: {ai['reader_engagement']}")

    if stats:
        ending = stats.get("ending_style", {})
        if ending:
            dominant = max(ending, key=ending.get) if ending else ""
            parts.append(f"\n[통계적 특징]")
            parts.append(f"- 평균 글 길이: {stats.get('avg_post_length', 'N/A')}자")
            parts.append(f"- 평균 문장 길이: {stats.get('avg_sentence_length', 'N/A')}자")
            parts.append(f"- 글당 평균 문단 수: {stats.get('avg_paragraphs_per_post', 'N/A')}개")
            parts.append(f"- 주요 종결어미: {dominant} ({ending.get(dominant, 0)}%)")

            style_details = [f"{k}: {v}%" for k, v in ending.items() if v > 0]
            parts.append(f"- 종결어미 분포: {', '.join(style_details)}")

        freq_words = stats.get("frequent_words", [])
        if freq_words:
            top_words = [item["word"] for item in freq_words[:15]]
            parts.append(f"- 자주 사용하는 단어: {', '.join(top_words)}")

    parts.append("\n[중요 규칙]")
    parts.append("- 위 분석 결과에 기반하여 원래 블로거가 직접 쓴 것처럼 자연스러운 글을 작성하세요.")
    parts.append("- 어색하거나 기계적인 표현을 피하세요.")
    parts.append("- 블로거 고유의 표현 방식과 톤을 유지하세요.")

    return "\n".join(parts)


def _build_reference_prompt(reference_text: str) -> str:
    """Build a prompt section that instructs the model to mimic a specific reference document's style."""
    truncated = reference_text[:6000]
    return f"""
[참조 문서 스타일]
아래 참조 문서의 문체, 톤, 구조, 표현 방식을 특별히 참고하여 글을 작성해주세요.
참조 문서의 내용을 그대로 복사하지 말고, 그 문서가 보여주는 문장 스타일, 감성, 호흡, 서술 방식을 본문에 녹여주세요.

--- 참조 문서 ---
{truncated}
--- 참조 문서 끝 ---
"""


async def generate_blog_post(
    topic: str,
    style_profile: dict,
    length: str = "medium",
    additional_instructions: str = "",
    reference_text: str = "",
    reference_url: str = "",
) -> dict:
    """Generate a blog post using Gemini API with the style profile."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        return {"error": "GOOGLE_API_KEY가 설정되지 않았습니다."}

    length_guide = {
        "short": "800~1200자",
        "medium": "1500~2500자",
        "long": "3000~5000자",
    }
    target_length = length_guide.get(length, length_guide["medium"])

    system_prompt = _build_style_prompt(style_profile)

    if reference_text:
        system_prompt += "\n" + _build_reference_prompt(reference_text)

    user_prompt = f"""다음 주제로 블로그 글을 작성해주세요.

주제: {topic}
목표 길이: {target_length}

{f"추가 지시사항: {additional_instructions}" if additional_instructions else ""}

제목도 함께 작성해주세요. 다음 형식으로 응답해주세요:

제목: [글 제목]

[본문 내용]"""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Content(role="user", parts=[types.Part(text=system_prompt)]),
                types.Content(role="model", parts=[types.Part(text="네, 해당 블로거의 문체를 완벽히 이해했습니다. 분석된 스타일대로 글을 작성하겠습니다.")]),
                types.Content(role="user", parts=[types.Part(text=user_prompt)]),
            ],
            config=types.GenerateContentConfig(
                temperature=0.8,
                max_output_tokens=8192,
            ),
        )
        text = response.text.strip()

        title_match = re.match(r'^제목:\s*(.+?)(?:\n|$)', text)
        if title_match:
            generated_title = title_match.group(1).strip()
            body = text[title_match.end():].strip()
        else:
            lines = text.split('\n', 1)
            generated_title = lines[0].strip().lstrip('#').strip()
            body = lines[1].strip() if len(lines) > 1 else text

        result = {
            "title": generated_title,
            "content": body,
            "topic": topic,
            "length": length,
            "char_count": len(body),
        }
        if reference_url:
            result["reference_url"] = reference_url
        return result
    except Exception as e:
        return {"error": f"글 생성 실패: {str(e)}"}
