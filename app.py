"""
Podcast Generator - Streamlit Web Application

Generate podcast audio from any topic using AI-powered scripting and TTS.
"""

import os
import tempfile

import streamlit as st

from utils import (
    check_ffmpeg,
    generate_podcast_audio,
    generate_script,
    generate_script_streaming,
    search_web,
    summarize_search_results,
)


# Page configuration
st.set_page_config(
    page_title="AI 팟캐스트 생성기",
    page_icon="🎙️",
    layout="centered"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .stProgress > div > div > div > div {
        background-color: #1E88E5;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Main application entry point."""
    
    # Sidebar for API Keys
    with st.sidebar:
        st.header("🔑 API 설정")
        
        gemini_api_key = st.text_input(
            "Google Gemini API Key",
            type="password",
            help="Gemini 2.0 Flash를 사용하기 위한 API 키를 입력하세요."
        )
        
        tavily_api_key = st.text_input(
            "Tavily API Key",
            type="password",
            help="웹 검색을 위한 Tavily API 키를 입력하세요."
        )
        
        st.divider()
        
        st.markdown("""
        ### 사용 방법
        1. API 키를 입력하세요
        2. 원하는 팟캐스트 주제를 입력하세요
        3. '팟캐스트 생성하기' 버튼을 클릭하세요
        4. 생성된 오디오를 듣거나 다운로드하세요
        """)
        
        st.divider()
        
        # ffmpeg check
        if not check_ffmpeg():
            st.warning("""
            ⚠️ **ffmpeg가 설치되지 않았습니다**
            
            오디오 생성을 위해 ffmpeg가 필요합니다.
            
            **설치 방법:**
            - Mac: `brew install ffmpeg`
            - Ubuntu: `sudo apt-get install ffmpeg`
            """)
    
    # Main content
    st.markdown('<p class="main-header">🎙️ AI 팟캐스트 생성기</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">주제를 입력하면 AI가 대본을 작성하고 자연스러운 대화 팟캐스트를 만들어 드립니다</p>',
        unsafe_allow_html=True
    )
    
    # Topic input
    topic = st.text_input(
        "팟캐스트 주제",
        placeholder="예: 인공지능의 미래, 기후변화와 환경, 우주 탐사의 역사...",
        help="생성하고 싶은 팟캐스트의 주제를 자유롭게 입력하세요."
    )
    
    # Generate button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        generate_button = st.button(
            "🎤 팟캐스트 생성하기",
            type="primary",
            use_container_width=True
        )
    
    # Initialize session state for results
    if "generated_script" not in st.session_state:
        st.session_state.generated_script = None
    if "generated_audio" not in st.session_state:
        st.session_state.generated_audio = None
    if "generated_topic" not in st.session_state:
        st.session_state.generated_topic = None
    
    # Generation logic
    if generate_button:
        # Validation
        if not gemini_api_key:
            st.error("❌ Gemini API 키를 입력해주세요.")
            return
        
        if not tavily_api_key:
            st.error("❌ Tavily API 키를 입력해주세요.")
            return
        
        if not topic.strip():
            st.error("❌ 팟캐스트 주제를 입력해주세요.")
            return
        
        if not check_ffmpeg():
            st.error("❌ ffmpeg가 설치되어 있지 않습니다. 사이드바의 안내를 참고해주세요.")
            return
        
        # Progress tracking
        progress_container = st.container()
        
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Container for live script preview
            script_preview_container = st.empty()
        
        try:
            # Step 1: Web Search
            status_text.markdown("🔍 **Step 1/4: 관련 정보를 검색하는 중...**")
            progress_bar.progress(10)
            
            search_results = search_web(topic, tavily_api_key)
            progress_bar.progress(20)
            
            status_text.markdown("✅ 검색 완료! 관련 자료를 찾았습니다.")
            
            # Step 2: Summarize search results
            status_text.markdown("📋 **Step 2/4: 검색 결과를 정리하는 중... (Gemini 2.0 Flash)**")
            progress_bar.progress(25)
            
            with st.spinner("검색 결과를 정리하고 있습니다..."):
                summarized_results = summarize_search_results(topic, search_results, gemini_api_key)
            
            progress_bar.progress(35)
            status_text.markdown("✅ 자료 정리 완료!")
            
            # Step 3: Script Generation
            status_text.markdown("✍️ **Step 3/4: AI가 팟캐스트 대본을 작성하는 중... (Gemini 2.0 Flash)**")
            progress_bar.progress(40)
            
            with script_preview_container.container():
                st.markdown("##### 📝 대본 생성 중...")
                with st.spinner("Gemini가 대본을 작성하고 있습니다..."):
                    script = generate_script(topic, summarized_results, gemini_api_key)
            
            progress_bar.progress(60)
            status_text.markdown("✅ 대본 작성 완료!")
            
            # Clear the preview
            script_preview_container.empty()
            
            # Step 4: Audio Generation
            status_text.markdown("🎵 **Step 4/4: 음성을 생성하는 중...**")
            progress_bar.progress(65)
            
            audio_status = st.empty()
            audio_status.info("🎤 음성 합성을 준비하고 있습니다...")
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                audio_path = tmp_file.name
            
            audio_status.info("🎤 Host와 Guest의 대화를 음성으로 변환하는 중... (약 30초~1분 소요)")
            
            generate_podcast_audio(script, audio_path)
            progress_bar.progress(95)
            
            # Read audio bytes and store in session state
            with open(audio_path, "rb") as audio_file:
                audio_bytes = audio_file.read()
            
            # Save results to session state
            st.session_state.generated_script = script
            st.session_state.generated_audio = audio_bytes
            st.session_state.generated_topic = topic
            
            audio_status.success("✅ 음성 합성 완료!")
            progress_bar.progress(100)
            status_text.markdown("🎉 **팟캐스트 생성 완료!**")
            
            # Clean up temp file
            try:
                os.unlink(audio_path)
            except:
                pass
                
        except Exception as e:
            progress_bar.progress(100)
            status_text.markdown("")
            st.error(f"❌ 오류가 발생했습니다: {str(e)}")
    
    # Display results from session state (persists across reruns)
    if st.session_state.generated_script and st.session_state.generated_audio:
        saved_topic = st.session_state.generated_topic or "podcast"
        
        st.success("🎉 팟캐스트가 성공적으로 생성되었습니다!")
        
        # Audio player
        st.subheader("🎧 생성된 팟캐스트")
        st.audio(st.session_state.generated_audio, format="audio/mp3")
        
        # Audio download button
        st.download_button(
            label="📥 오디오 다운로드",
            data=st.session_state.generated_audio,
            file_name=f"podcast_{saved_topic[:20].replace(' ', '_')}.mp3",
            mime="audio/mp3"
        )
        
        # Script display
        with st.expander("📝 생성된 대본 보기", expanded=False):
            st.text(st.session_state.generated_script)
        
        # Script save (download) button
        st.download_button(
            label="💾 대본 저장",
            data=st.session_state.generated_script,
            file_name=f"podcast_script_{saved_topic[:20].replace(' ', '_')}.txt",
            mime="text/plain"
        )


if __name__ == "__main__":
    main()
