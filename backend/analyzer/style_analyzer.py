import re
import os
from collections import Counter
from google import genai
from google.genai import types


def _split_sentences(text: str) -> list[str]:
    """Split Korean text into sentences."""
    sentences = re.split(r'[.!?。]+\s*', text)
    return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 2]


def _split_paragraphs(text: str) -> list[str]:
    parts = re.split(r'\n\s*\n|\n', text)
    return [p.strip() for p in parts if p.strip() and len(p.strip()) > 5]


def _detect_ending_style(sentences: list[str]) -> dict:
    """Detect sentence ending patterns (해요체, 합니다체, 반말 등)."""
    patterns = {
        "합니다체": r'(합니다|됩니다|있습니다|없습니다|했습니다|입니다|봅니다|갑니다|옵니다)\s*[.!?]?\s*$',
        "해요체": r'(해요|돼요|있어요|없어요|했어요|이에요|예요|네요|군요|거든요|잖아요|나요|세요|볼게요|할게요)\s*[.!?]?\s*$',
        "반말": r'(한다|된다|있다|없다|했다|이다|보다|간다|온다)\s*[.!?]?\s*$',
        "명사형종결": r'(것|듯|수|중|뿐)\s*[.!?]?\s*$',
        "감탄/의문": r'[!?]+\s*$',
    }

    counts: dict[str, int] = {k: 0 for k in patterns}
    for sent in sentences:
        for style, pat in patterns.items():
            if re.search(pat, sent):
                counts[style] += 1
                break

    total = max(sum(counts.values()), 1)
    return {k: round(v / total * 100, 1) for k, v in counts.items()}


def _get_frequent_words(texts: list[str], top_n: int = 30) -> list[tuple[str, int]]:
    """Extract frequently used words (2+ chars, not pure numbers)."""
    all_words: list[str] = []
    for text in texts:
        words = re.findall(r'[가-힣a-zA-Z]{2,}', text)
        all_words.extend(words)

    stopwords = {
        "그리고", "하지만", "그러나", "그래서", "때문에", "그런데", "그래도",
        "하는", "있는", "없는", "것이", "수가", "되는", "하고", "에서",
        "으로", "이런", "저런", "그런", "이것", "저것", "것을", "에게",
    }
    filtered = [w for w in all_words if w not in stopwords]
    return Counter(filtered).most_common(top_n)


def _get_frequent_expressions(texts: list[str], top_n: int = 15) -> list[tuple[str, int]]:
    """Extract recurring 2-3 word phrases."""
    all_phrases: list[str] = []
    for text in texts:
        words = re.findall(r'[가-힣a-zA-Z]+', text)
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i+1]}"
            if len(bigram) > 4:
                all_phrases.append(bigram)
    return Counter(all_phrases).most_common(top_n)


def statistical_analysis(posts: list[dict]) -> dict:
    """Perform statistical analysis on collected posts."""
    all_sentences: list[str] = []
    all_paragraphs: list[str] = []
    all_contents: list[str] = []
    post_lengths: list[int] = []
    emoji_count = 0

    for post in posts:
        content = post.get("content", "")
        if not content:
            continue
        all_contents.append(content)
        sents = _split_sentences(content)
        paras = _split_paragraphs(content)
        all_sentences.extend(sents)
        all_paragraphs.extend(paras)
        post_lengths.append(len(content))
        emoji_count += len(re.findall(
            r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF'
            r'\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U0001F900-\U0001F9FF'
            r'\U0001FA00-\U0001FA6F]+',
            content
        ))

    if not all_sentences:
        return {"error": "분석할 문장이 없습니다."}

    sent_lengths = [len(s) for s in all_sentences]
    para_lengths = [len(p) for p in all_paragraphs]

    return {
        "total_posts": len(posts),
        "avg_post_length": round(sum(post_lengths) / max(len(post_lengths), 1)),
        "total_sentences": len(all_sentences),
        "avg_sentence_length": round(sum(sent_lengths) / max(len(sent_lengths), 1), 1),
        "min_sentence_length": min(sent_lengths) if sent_lengths else 0,
        "max_sentence_length": max(sent_lengths) if sent_lengths else 0,
        "avg_paragraph_length": round(sum(para_lengths) / max(len(para_lengths), 1), 1),
        "avg_paragraphs_per_post": round(len(all_paragraphs) / max(len(posts), 1), 1),
        "ending_style": _detect_ending_style(all_sentences),
        "frequent_words": [{"word": w, "count": c} for w, c in _get_frequent_words(all_contents)],
        "frequent_expressions": [{"phrase": p, "count": c} for p, c in _get_frequent_expressions(all_contents)],
        "emoji_total": emoji_count,
        "emoji_per_post": round(emoji_count / max(len(posts), 1), 1),
    }


async def ai_analysis(posts: list[dict]) -> dict:
    """Use Gemini to perform qualitative style analysis."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        return {"error": "GOOGLE_API_KEY가 설정되지 않았습니다. backend/.env 파일을 확인해주세요."}

    sample_posts = posts[:10]
    sample_text = ""
    for i, post in enumerate(sample_posts, 1):
        title = post.get("title", "제목 없음")
        content = post.get("content", "")[:2000]
        sample_text += f"\n--- 글 {i}: {title} ---\n{content}\n"

    prompt = f"""다음은 한 블로거가 작성한 블로그 글 샘플입니다. 이 블로거의 문체와 스타일을 상세히 분석해주세요.

{sample_text}

다음 항목에 대해 분석해주세요. 반드시 JSON 형식으로만 응답하세요:

{{
  "overall_tone": "전체적인 톤 (예: 따뜻한, 차분한, 유머러스한 등)",
  "writing_persona": "글쓴이의 페르소나/캐릭터 설명",
  "narrative_style": "서술 방식 특징 (1인칭/3인칭, 대화체 여부 등)",
  "vocabulary_level": "어휘 수준 (쉬운/보통/전문적)",
  "sentence_structure": "문장 구조 특징",
  "paragraph_organization": "문단 구성 방식",
  "rhetorical_devices": ["자주 사용하는 수사법 목록"],
  "emotional_expression": "감정 표현 방식",
  "topic_transition": "주제 전환 방식",
  "opening_pattern": "글 시작 패턴",
  "closing_pattern": "글 마무리 패턴",
  "unique_characteristics": ["이 블로거만의 독특한 특징들"],
  "content_themes": ["주로 다루는 주제/테마"],
  "reader_engagement": "독자와의 소통 방식"
}}"""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=8192,
                response_mime_type="application/json",
            ),
        )
        text = response.text.strip()
        import json
        return json.loads(text)
    except Exception as e:
        raw = ""
        try:
            raw = text[:300]
        except Exception:
            pass
        return {"error": f"AI 분석 실패: {str(e)}", "raw_response": raw}


async def full_analysis(posts: list[dict]) -> dict:
    """Run both statistical and AI analysis."""
    stats = statistical_analysis(posts)
    ai_result = await ai_analysis(posts)

    return {
        "statistical": stats,
        "ai_analysis": ai_result,
    }
