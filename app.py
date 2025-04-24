import os
import time
import requests
from io import BytesIO
import streamlit as st
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

# Load env variables
load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

API_URL = "https://api.sync.so/v2/generate"
SYNC_API_KEY = os.getenv("API_KEY")

# --- Sample Media Links (Replace with yours) ---
SAMPLE_AUDIOS = {
    "Sample Audio 1": "https://res.cloudinary.com/dltnypl9l/video/upload/v1745502217/lipsync_app/voice1.wav",
    "Sample Audio 2": "https://res.cloudinary.com/dltnypl9l/video/upload/v1745502182/lipsync_app/How%20virus%20is%20created%20webdevelopment%20frontend%20html%20css%20javascript%20coding%20javascripttricks%20-%20Yashu%20Developer-%5BAudioTrimmer.wav",
    "Sample Audio 3": "https://res.cloudinary.com/dltnypl9l/video/upload/v1745502088/lipsync_app/5_50%20Frontend%20Technologies%20Build%20Beautiful%20UIs%20with%20shadcn_ui%20-%20Sheryians%20Coding%20School-%5BAudioTrimmer.wav",
    "Sample Audio 4": "https://res.cloudinary.com/dltnypl9l/video/upload/v1745502065/lipsync_app/The%20Most%20GOATED%20Pitch%20on%20Shark%20Tank-%5BAudioTrimmer.wav",
}

SAMPLE_VIDEOS = {
    "Sample Video 1": "https://res.cloudinary.com/dltnypl9l/video/upload/v1745502214/lipsync_app/mona.mp4",
    "Sample Video 2": "https://res.cloudinary.com/dltnypl9l/video/upload/v1745502180/lipsync_app/sync.mov",
    "Sample Video 3": "https://res.cloudinary.com/dltnypl9l/video/upload/v1745502087/lipsync_app/women.mp4",
    "Sample Video 4": "https://res.cloudinary.com/dltnypl9l/video/upload/v1745502063/lipsync_app/old_man.mp4",
}

# --- App Configuration ---
st.set_page_config(page_title="LipSync Generator", layout="wide")
st.title("🗣️➡️🎥 LipSync Video Generator")
st.markdown("Choose from **sample media** or upload your own files to generate a lip-synced video.")

# --- Sample Video Preview Section ---
st.subheader("🎬 Select Sample Video")
video_container = st.container()
with video_container:
    video_cols = st.columns(len(SAMPLE_VIDEOS))
    for i, (label, url) in enumerate(SAMPLE_VIDEOS.items()):
        with video_cols[i]:
            st.video(url)
            if st.button(f"Use {label}", key=f"video_{i}"):
                st.session_state["selected_video_url"] = url
                st.session_state.pop("uploaded_video", None)

# --- Sample Audio Preview Section ---
st.subheader("🎵 Select Sample Audio")
audio_container = st.container()
with audio_container:
    audio_cols = st.columns(len(SAMPLE_AUDIOS))
    for i, (label, url) in enumerate(SAMPLE_AUDIOS.items()):
        with audio_cols[i]:
            st.audio(url)
            if st.button(f"Use {label}", key=f"audio_{i}"):
                st.session_state["selected_audio_url"] = url
                st.session_state.pop("uploaded_audio", None)

# --- File Upload Section ---
st.markdown("---")
st.subheader("📤 Or Upload Your Own Files")
upload_cols = st.columns(2)

with upload_cols[0]:
    uploaded_video = st.file_uploader("🎥 Upload Video", type=["mp4", "mov"])
    if uploaded_video:
        st.video(uploaded_video)
        st.session_state["uploaded_video"] = uploaded_video
        st.session_state.pop("selected_video_url", None)

with upload_cols[1]:
    uploaded_audio = st.file_uploader("🎵 Upload Audio", type=["mp3", "wav"])
    if uploaded_audio:
        st.audio(uploaded_audio)
        st.session_state["uploaded_audio"] = uploaded_audio
        st.session_state.pop("selected_audio_url", None)

# --- Generate Button ---
st.markdown("---")
if st.button("🚀 Generate Lip-Synced Video", use_container_width=True):
    video_file = st.session_state.get("uploaded_video")
    audio_file = st.session_state.get("uploaded_audio")
    video_url = st.session_state.get("selected_video_url")
    audio_url = st.session_state.get("selected_audio_url")

    if not (video_file or video_url) or not (audio_file or audio_url):
        st.warning("Please upload or select both **audio** and **video** files.")
        st.stop()

    with st.spinner("Uploading files and generating video..."):
        headers = {
            "x-api-key": SYNC_API_KEY,
            "Content-Type": "application/json"
        }

        # Upload if necessary
        if video_file:
            try:
                video_bytes = BytesIO(video_file.read())
                video_upload = cloudinary.uploader.upload_large(
                    video_bytes,
                    resource_type="video",
                    folder="lipsync_app",
                    public_id=video_file.name.split('.')[0]
                )
                video_url = video_upload["secure_url"]
            except Exception as e:
                st.error(f"Video upload failed: {e}")
                st.stop()

        if audio_file:
            try:
                audio_bytes = BytesIO(audio_file.read())
                audio_upload = cloudinary.uploader.upload(
                    audio_bytes,
                    resource_type="video",
                    folder="lipsync_app",
                    public_id=audio_file.name.split('.')[0]
                )
                audio_url = audio_upload["secure_url"]
            except Exception as e:
                st.error(f"Audio upload failed: {e}")
                st.stop()

        payload = {
            "model": "lipsync-1.8.0",
            "options": {
                "output_format": "mp4"
            },
            "input": [
                {"type": "video", "url": video_url},
                {"type": "audio", "url": audio_url}
            ]
        }

        try:
            response = requests.post(API_URL, headers=headers, json=payload)
        except Exception as e:
            st.error(f"Failed to connect to API: {e}")
            st.stop()

        if response.status_code != 201:
            st.error(f"API Error: {response.text}")
            st.stop()

        job_id = response.json()["id"]
        output_url = None

        while True:
            time.sleep(10)
            poll = requests.get(f"{API_URL}/{job_id}", headers=headers)
            result = poll.json()
            if result["status"] == "COMPLETED":
                output_url = result["outputUrl"]
                break
            elif result["status"] == "FAILED":
                st.error("API processing failed.")
                st.stop()

        st.success("✅ Lip-synced video is ready!")
        st.video(output_url)
