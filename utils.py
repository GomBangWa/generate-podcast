"""
Utility functions for podcast generation.
Handles web search, script generation, and audio synthesis.
"""

import asyncio
import os
import re
import tempfile
from typing import Any, List, Tuple

import edge_tts
import google.generativeai as genai
from pydub import AudioSegment  # type: ignore[import-untyped]
from tavily import TavilyClient


# Edge-TTS voice configurations for Korean
HOST_VOICE = "ko-KR-InJoonNeural"  # Male voice for Host
GUEST_VOICE = "ko-KR-SunHiNeural"  # Female voice for Guest


def search_web(query: str, tavily_api_key: str, max_results: int = 5) -> str:
    """
    Search the web for information about the given query using Tavily.
    
    Args:
        query: The search topic/query.
        tavily_api_key: Tavily API key for authentication.
        max_results: Maximum number of search results (default: 5).
        
    Returns:
        Concatenated text content from search results.
        
    Raises:
        Exception: If search fails.
    """
    client = TavilyClient(api_key=tavily_api_key)
    
    response = client.search(
        query=query,
        search_depth="advanced",
        max_results=max_results,
        include_answer=True
    )
    
    # Combine all search results into a single text
    combined_text = ""
    
    if response.get("answer"):
        combined_text += f"요약: {response['answer']}\n\n"
    
    for i, result in enumerate(response.get("results", []), 1):
        title = result.get("title", "제목 없음")
        content = result.get("content", "")
        url = result.get("url", "")
        combined_text += f"[자료 {i}] {title}\n출처: {url}\n내용: {content}\n\n"
    
    return combined_text


def summarize_search_results(topic: str, search_results: str, gemini_api_key: str) -> str:
    """
    Summarize and organize raw search results using Gemini 2.0 Flash.
    
    Args:
        topic: The podcast topic.
        search_results: Raw search results text.
        gemini_api_key: Google Gemini API key.
        
    Returns:
        Organized and summarized search information.
    """
    genai.configure(api_key=gemini_api_key)
    
    model = genai.GenerativeModel("gemini-2.0-flash")
    
    prompt = f"""다음은 "{topic}"에 대한 웹 검색 결과입니다. 이 정보를 정리하고 요약해주세요.

검색 결과:
{search_results}

다음 형식으로 정리해주세요:
1. 핵심 요약: 주제에 대한 전체적인 요약 (3-5문장)
2. 주요 포인트: 팟캐스트에서 다룰 만한 핵심 내용들 (bullet points)
3. 흥미로운 사실: 대화 소재로 활용할 수 있는 흥미로운 정보
4. 출처 정리: 참고한 주요 출처 목록

정리된 내용:"""
    
    response = model.generate_content(prompt)
    
    return response.text or search_results


def generate_script(topic: str, search_results: str, gemini_api_key: str) -> str:
    """
    Generate a podcast script using Gemini 2.0 Flash.
    
    Args:
        topic: The podcast topic.
        search_results: Background information from web search.
        gemini_api_key: Google Gemini API key.
        
    Returns:
        Generated podcast script in "Host: .../Guest: ..." format.
        
    Raises:
        Exception: If script generation fails.
    """
    genai.configure(api_key=gemini_api_key)
    
    model = genai.GenerativeModel("gemini-2.0-flash")
    
    prompt = _build_script_prompt(topic, search_results)
    
    response = model.generate_content(prompt)
    
    return response.text


def generate_script_streaming(topic: str, search_results: str, gemini_api_key: str):
    """
    Generate a podcast script using Gemini with streaming for real-time display.
    
    Args:
        topic: The podcast topic.
        search_results: Background information from web search.
        gemini_api_key: Google Gemini API key.
        
    Yields:
        str: Chunks of the generated script as they become available.
    """
    genai.configure(api_key=gemini_api_key)
    
    model = genai.GenerativeModel("gemini-2.0-flash")
    
    prompt = _build_script_prompt(topic, search_results)
    
    response = model.generate_content(prompt, stream=True)
    
    for chunk in response:
        if chunk.text:
            yield chunk.text


def _build_script_prompt(topic: str, search_results: str) -> str:
    """Build the prompt for script generation."""
    return f"""당신은 전문 팟캐스트 작가입니다. 다음 주제와 자료를 바탕으로 흥미롭고 자연스러운 2인 대화 팟캐스트 대본을 작성해주세요.

주제: {topic}

참고 자료:
{search_results}

대본 작성 규칙:
1. Host(진행자)와 Guest(게스트 전문가) 두 명의 대화로 구성하세요.
2. 자연스럽고 친근한 대화체를 사용하세요.
3. 주제에 대한 핵심 정보를 재미있게 전달하세요.
4. 대화는 5-10분 분량(약 15-25개의 대화 턴)으로 작성하세요.
5. 반드시 다음 형식으로 작성하세요:

Host: [진행자의 대사]
Guest: [게스트의 대사]
Host: [진행자의 대사]
...

대본을 시작하세요:"""


def parse_script(script: str) -> List[Tuple[str, str]]:
    """
    Parse the podcast script into speaker-text pairs.
    
    Args:
        script: The raw script text with "Host:/Guest:" format.
        
    Returns:
        List of (speaker, text) tuples.
    """
    # Pattern to match "Host:" or "Guest:" followed by their lines
    pattern = r'(Host|Guest):\s*(.+?)(?=(?:Host|Guest):|$)'
    matches = re.findall(pattern, script, re.DOTALL | re.IGNORECASE)
    
    parsed = []
    for speaker, text in matches:
        # Clean up the text
        cleaned_text = text.strip()
        if cleaned_text:
            parsed.append((speaker.capitalize(), cleaned_text))
    
    return parsed


async def _generate_single_audio(text: str, voice: str, output_path: str) -> None:
    """
    Generate audio for a single text segment using Edge-TTS.
    
    Args:
        text: Text to convert to speech.
        voice: Voice identifier for Edge-TTS.
        output_path: Path to save the audio file.
    """
    communicate = edge_tts.Communicate(text, voice, rate="+20%")
    await communicate.save(output_path)


def generate_podcast_audio(script: str, output_path: str = "podcast.mp3") -> str:
    """
    Generate complete podcast audio from script.
    
    Args:
        script: The podcast script in "Host:/Guest:" format.
        output_path: Path for the final audio file.
        
    Returns:
        Path to the generated audio file.
        
    Raises:
        RuntimeError: If ffmpeg is not installed or audio processing fails.
    """
    # Parse the script
    parsed_script = parse_script(script)
    
    if not parsed_script:
        raise ValueError("대본을 파싱할 수 없습니다. 올바른 형식인지 확인해주세요.")
    
    # Create a temporary directory for intermediate files
    temp_dir = tempfile.mkdtemp()
    audio_segments: List[Any] = []
    
    try:
        # Generate audio for each segment
        for i, (speaker, text) in enumerate(parsed_script):
            voice = HOST_VOICE if speaker == "Host" else GUEST_VOICE
            temp_file = os.path.join(temp_dir, f"segment_{i}.mp3")
            
            # Run async TTS generation
            asyncio.run(_generate_single_audio(text, voice, temp_file))
            
            # Load the audio segment
            try:
                segment = AudioSegment.from_mp3(temp_file)
                audio_segments.append(segment)
                
                # Add a short pause between speakers (500ms)
                pause = AudioSegment.silent(duration=500)
                audio_segments.append(pause)
            except Exception as e:
                raise RuntimeError(
                    f"오디오 처리 중 오류가 발생했습니다. "
                    f"ffmpeg가 설치되어 있는지 확인해주세요.\n"
                    f"설치 방법 (Mac): brew install ffmpeg\n"
                    f"설치 방법 (Ubuntu): sudo apt-get install ffmpeg\n"
                    f"오류 상세: {str(e)}"
                )
        
        # Combine all segments
        if audio_segments:
            combined = audio_segments[0]
            for segment in audio_segments[1:]:  # type: ignore[index]
                combined = combined + segment
            
            # Export the final audio
            combined.export(output_path, format="mp3")
        
        return output_path
        
    finally:
        # Clean up temporary files
        for f in os.listdir(temp_dir):
            try:
                os.remove(os.path.join(temp_dir, f))
            except:
                pass
        try:
            os.rmdir(temp_dir)
        except:
            pass


def check_ffmpeg() -> bool:
    """
    Check if ffmpeg is installed on the system.
    
    Returns:
        True if ffmpeg is available, False otherwise.
    """
    import shutil
    return shutil.which("ffmpeg") is not None
