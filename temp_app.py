import os
import time
import requests
from io import BytesIO
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

job_id = "4efc5277-4b33-488d-9e2e-4a246dbcbd58"
api_key = os.getenv("API_KEY")
headers = {
    "x-api-key": api_key,
    "Content-Type": "application/json"
}

output_url = None
while True:
    time.sleep(10)
    poll_response = requests.get(
        f"https://api.sync.so/v2/generate/{job_id}",
        headers=headers
    )
    job_data = poll_response.json()
    if job_data["status"] == "COMPLETED":
        output_url = job_data["outputUrl"]
        break

if output_url:
    st.success("✅ Lip-synced video is ready!")

    with st.container():
        st.markdown("### 🆕 Generated Video")
        st.video(output_url)
        if st.button("📥 Download Video"):
            try:
                with st.spinner("Downloading video..."):
                    video_response = requests.get(output_url)
                    video_bytes = BytesIO(video_response.content)

                st.download_button(
                    label="✅ Click to Save Video",
                    data=video_bytes,
                    file_name="lip_synced_result.mp4",
                    mime="video/mp4"
                )
            except Exception as e:
                st.error(f"Couldn't prepare video for download: {e}")
