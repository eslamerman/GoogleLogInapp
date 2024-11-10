import streamlit as st
import boto3
import tempfile
from moviepy.editor import VideoFileClip
import speech_recognition as sr

# Initialize S3 client
s3_client = boto3.client('s3')

# Function to upload video to S3
def upload_to_s3(file, bucket_name, s3_key):
    s3_client.upload_fileobj(file, bucket_name, s3_key)
    return f"File uploaded successfully to S3 at {s3_key}"

# Function to process video and extract audio
def extract_audio_from_video(video_file):
    # Create a temporary file to store the audio
    with tempfile.NamedTemporaryFile(delete=False) as temp_audio_file:
        temp_audio_file_path = temp_audio_file.name
        
    # Load the video file using moviepy
    video = VideoFileClip(video_file)
    
    # Extract audio from the video clip
    audio = video.audio
    audio.write_audiofile(temp_audio_file_path, codec='pcm_s16le')  # Save the audio to the temporary file
    return temp_audio_file_path

# Function to convert speech to text
def audio_to_text(audio_file):
    recognizer = sr.Recognizer()
    audio = sr.AudioFile(audio_file)
    
    with audio as source:
        audio_data = recognizer.record(source)
        
    try:
        text = recognizer.recognize_google(audio_data)
        return text
    except sr.UnknownValueError:
        return "Could not understand the audio."
    except sr.RequestError:
        return "Could not request results from Google Speech Recognition service."

# Streamlit UI setup
st.title("Video to Text Converter")

# Allow the user to upload a video (less than 200 MB)
uploaded_video = st.file_uploader("Upload a Video", type=["mp4", "avi", "mov"], accept_multiple_files=False)

# Check video size limit (less than 200MB)
if uploaded_video:
    video_size_mb = uploaded_video.size / (1024 * 1024)  # Convert bytes to MB
    if video_size_mb > 200:
        st.warning("The file is too large! Please upload a video smaller than 200 MB.")
    else:
        st.video(uploaded_video)  # Show the video to the user
        
        # Process the video to extract text
        st.spinner("Processing video... please wait.")
        
        # Save uploaded video to a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_video_file:
            temp_video_file.write(uploaded_video.read())
            temp_video_path = temp_video_file.name
        
        # Upload the video file to S3
        upload_status = upload_to_s3(uploaded_video, "your-bucket-name", "uploaded-video.mp4")
        st.success(upload_status)

        # Extract audio from the video
        audio_path = extract_audio_from_video(temp_video_path)
        
        # Extract text from the audio
        text = audio_to_text(audio_path)
        
        # Display the extracted text
        st.subheader("Extracted Text:")
        st.write(text)
