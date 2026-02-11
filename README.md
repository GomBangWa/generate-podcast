# 🎙️ AI 팟캐스트 생성기

주제를 입력하면 AI가 자동으로 정보를 수집하고, 대본을 작성하고, 음성으로 변환하여 2인 대화 팟캐스트를 생성하는 웹 애플리케이션입니다.

![AI 팟캐스트 생성기](app_image.png)

---

## 주요 기능

| 단계 | 설명 | 사용 기술 |
|------|------|-----------|
| 🔍 정보 수집 | 주제에 대한 웹 검색 및 자료 수집 | Tavily API |
| 📋 자료 정리 | 검색 결과를 핵심 포인트로 요약 | Gemini 2.0 Flash |
| ✍️ 대본 생성 | Host/Guest 2인 대화 형식의 팟캐스트 대본 작성 | Gemini 2.0 Flash |
| 🎤 TTS 변환 | 대본을 자연스러운 한국어 음성으로 합성 | Edge-TTS |

## 기술 스택

- **Frontend**: Streamlit
- **LLM**: Google Gemini 2.0 Flash
- **웹 검색**: Tavily API
- **음성 합성**: Edge-TTS (Microsoft, 무료)
- **오디오 처리**: Pydub + FFmpeg

## 설치 및 실행

### 1. 사전 요구사항

- Python 3.11+
- FFmpeg

```bash
# FFmpeg 설치 (Mac)
brew install ffmpeg

# FFmpeg 설치 (Ubuntu)
sudo apt-get install ffmpeg
```

### 2. 프로젝트 설정

```bash
git clone https://github.com/GomBangWa/generate-podcast.git
cd generate-podcast

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

### 3. 실행

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501`로 접속합니다.

### 4. API 키 입력

사이드바에서 다음 API 키를 입력합니다:

- **Google Gemini API Key**: [Google AI Studio](https://aistudio.google.com/apikey)에서 발급
- **Tavily API Key**: [Tavily](https://tavily.com/)에서 발급

## 처리 흐름

```
주제 입력 → Tavily 웹 검색 → Gemini 자료 정리 → Gemini 대본 생성 → Edge-TTS 음성 합성 → MP3 출력
```

## 프로젝트 구조

```
generate-podcast/
├── app.py              # Streamlit 웹 UI
├── utils.py            # 핵심 로직 (검색, LLM, TTS)
├── requirements.txt    # 의존성 패키지
└── .gitignore
```

## 라이선스

MIT License
