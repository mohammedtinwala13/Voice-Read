"""
OCR Text-to-Speech App for Accessibility
Upload images, extract text, and listen to it via text-to-speech
Built with Streamlit + EasyOCR + gTTS for blind users
"""

import streamlit as st
from PIL import Image
import easyocr
import io
from gtts import gTTS
from pathlib import Path
import time
from typing import Optional, Tuple
import tempfile
import os


class TextExtractor:
    """Handles OCR text extraction from images"""
    
    def __init__(self):
        self.reader = None
    
    def initialize_reader(self):
        """Lazy load EasyOCR reader to save memory"""
        if self.reader is None:
            with st.spinner("🔄 Loading OCR model (first time only)..."):
                self.reader = easyocr.Reader(['en'])
        return self.reader
    
    def extract_text(self, image: Image.Image) -> Tuple[str, float]:
        """
        Extract text from image using EasyOCR
        
        Args:
            image: PIL Image object
            
        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        reader = self.initialize_reader()
        
        # Convert PIL to OpenCV format
        image_array = __import__('numpy').array(image)
        
        # Run OCR
        results = reader.readtext(image_array)
        
        # Extract text and calculate confidence
        extracted_text = '\n'.join([text for (_, text, confidence) in results])
        avg_confidence = sum(conf for (_, _, conf) in results) / len(results) if results else 0
        
        return extracted_text, avg_confidence


class AudioGenerator:
    """Handles text-to-speech conversion"""
    
    @staticmethod
    def text_to_speech(text: str, language: str = 'en') -> Optional[bytes]:
        """
        Convert text to speech using gTTS
        
        Args:
            text: Text to convert
            language: Language code (default 'en')
            
        Returns:
            Audio bytes in MP3 format
        """
        if not text or len(text.strip()) == 0:
            return None
        
        try:
            # Create TTS object
            tts = gTTS(text=text, lang=language, slow=False)
            
            # Save to bytes buffer
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            
            return audio_buffer.getvalue()
        except Exception as e:
            st.error(f"❌ Audio generation failed: {str(e)}")
            return None
    
    @staticmethod
    def save_audio_file(audio_bytes: bytes, filename: str = "extracted_text.mp3") -> str:
        """Save audio to temporary file for download"""
        if audio_bytes is None:
            return None
        
        # Create temp directory if it doesn't exist
        temp_dir = tempfile.gettempdir()
        filepath = os.path.join(temp_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(audio_bytes)
        
        return filepath


class UIManager:
    """Handles Streamlit UI configuration and layout"""
    
    @staticmethod
    def configure_page():
        """Configure Streamlit page settings"""
        st.set_page_config(
            page_title="VoiceRead - OCR to Speech",
            page_icon="👁️",
            layout="centered",
            initial_sidebar_state="collapsed",
        )
    
    @staticmethod
    def apply_custom_css():
        """Apply custom CSS for better accessibility and design"""
        st.markdown("""
        <style>
        /* Remove excess padding */
        .main {
            padding: 2rem 1rem;
            max-width: 900px;
            margin: 0 auto;
        }
        
        /* Typography */
        h1 {
            color: #1f3a93;
            text-align: center;
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            font-weight: 700;
            letter-spacing: -0.5px;
        }
        
        .subtitle {
            text-align: center;
            color: #666;
            font-size: 1.1rem;
            margin-bottom: 2rem;
            font-weight: 500;
        }
        
        /* Card styling */
        .upload-card {
            background: linear-gradient(135deg, #f0f4ff 0%, #f9f7ff 100%);
            border-left: 4px solid #1f3a93;
            padding: 1.5rem;
            border-radius: 8px;
            margin-bottom: 1.5rem;
        }
        
        .result-card {
            background: #f8f9fa;
            border: 1px solid #e0e4e8;
            padding: 1.5rem;
            border-radius: 8px;
            margin-bottom: 1.5rem;
        }
        
        .confidence-badge {
            display: inline-block;
            background: #e7f5e7;
            color: #2d7d2d;
            padding: 0.4rem 0.8rem;
            border-radius: 4px;
            font-size: 0.9rem;
            font-weight: 600;
            margin-bottom: 1rem;
        }
        
        /* Button improvements */
        .stButton > button {
            width: 100%;
            padding: 0.7rem 1.5rem;
            font-size: 1rem;
            font-weight: 600;
            border-radius: 6px;
            border: none;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        /* Success state */
        .success-text {
            color: #2d7d2d;
            font-weight: 600;
            margin-bottom: 1rem;
        }
        
        /* Error state */
        .error-text {
            color: #c41e3a;
            font-weight: 600;
        }
        
        /* Text area styling */
        .stTextArea textarea {
            font-size: 1rem;
            line-height: 1.6;
            border-radius: 6px;
        }
        
        /* Audio player */
        audio {
            width: 100%;
            margin-bottom: 1rem;
        }
        
        /* Accessibility: focus states */
        button:focus-visible {
            outline: 2px solid #1f3a93;
            outline-offset: 2px;
        }
        
        /* Loading state */
        .loading-text {
            text-align: center;
            color: #666;
            font-style: italic;
        }
        
        /* Info boxes */
        .info-box {
            background: #e7f5ff;
            border-left: 4px solid #0066cc;
            padding: 1rem;
            border-radius: 4px;
            margin-bottom: 1rem;
            font-size: 0.95rem;
            color: #333;
        }
        
        /* Spacing utilities */
        .spacer {
            margin-bottom: 2rem;
        }
        
        @media (max-width: 640px) {
            h1 {
                font-size: 2rem;
            }
            .main {
                padding: 1rem 0.5rem;
            }
        }
        </style>
        """, unsafe_allow_html=True)


class VoiceReadApp:
    """Main application class orchestrating the full workflow"""
    
    def __init__(self):
        self.extractor = TextExtractor()
        self.audio_gen = AudioGenerator()
        self.ui = UIManager()
        self.setup_session_state()
    
    def setup_session_state(self):
        """Initialize session state variables"""
        if 'extracted_text' not in st.session_state:
            st.session_state.extracted_text = ""
        if 'audio_bytes' not in st.session_state:
            st.session_state.audio_bytes = None
        if 'confidence' not in st.session_state:
            st.session_state.confidence = 0
    
    def render_header(self):
        """Render app header with title and description"""
        st.markdown("""
        <h1>👁️ VoiceRead</h1>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <p class="subtitle">Upload an image, extract text, and listen to it</p>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="info-box">
            <strong>♿ Accessibility First:</strong> Designed for blind and low-vision users. 
            Upload any image with text, and VoiceRead will read it aloud.
        </div>
        """, unsafe_allow_html=True)
    
    def render_upload_section(self) -> Optional[Image.Image]:
        """Render file upload section"""
        st.markdown("""
        <div class="upload-card">
            <h3>📤 Upload Image</h3>
            <p>Supported formats: PNG, JPG, JPEG (up to 10 MB)</p>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Choose an image file",
            type=['png', 'jpg', 'jpeg'],
            label_visibility="collapsed",
            help="Upload an image containing text you want to extract and hear"
        )
        
        if uploaded_file:
            try:
                image = Image.open(uploaded_file)
                
                # Validate image
                if image.size[0] < 50 or image.size[1] < 50:
                    st.warning("⚠️ Image too small. Please upload a larger image.")
                    return None
                
                return image
            except Exception as e:
                st.error(f"❌ Failed to load image: {str(e)}")
                return None
        
        return None
    
    def render_image_preview(self, image: Image.Image):
        """Display uploaded image"""
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(image, use_column_width=True, caption="📸 Your Image")
    
    def process_image(self, image: Image.Image) -> bool:
        """
        Process image and extract text
        
        Returns:
            True if successful, False otherwise
        """
        try:
            st.markdown("<div class='loading-text'>🔍 Extracting text from image...</div>", unsafe_allow_html=True)
            
            text, confidence = self.extractor.extract_text(image)
            
            if not text or len(text.strip()) == 0:
                st.warning("⚠️ No text found in the image. Try a clearer image.")
                return False
            
            # Store in session state
            st.session_state.extracted_text = text
            st.session_state.confidence = confidence
            
            return True
        except Exception as e:
            st.error(f"❌ OCR processing failed: {str(e)}")
            return False
    
    def render_results_section(self):
        """Render extracted text and audio controls"""
        if not st.session_state.extracted_text:
            return
        
        st.markdown("<div class='spacer'></div>", unsafe_allow_html=True)
        
        # Confidence badge
        confidence_pct = st.session_state.confidence * 100
        st.markdown(
            f'<span class="confidence-badge">✓ Confidence: {confidence_pct:.1f}%</span>',
            unsafe_allow_html=True
        )
        
        # Display extracted text
        st.markdown("<h3>📄 Extracted Text</h3>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="result-card">
            {st.session_state.extracted_text}
        </div>
        """, unsafe_allow_html=True)
        
        # Text area for editing (copy-friendly)
        st.text_area(
            "Edit text if needed:",
            value=st.session_state.extracted_text,
            height=150,
            key="edited_text",
            label_visibility="collapsed"
        )
        
        # Audio controls
        st.markdown("<h3>🔊 Text-to-Speech</h3>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🎙️ Generate Audio", use_container_width=True):
                text_to_speak = st.session_state.get('edited_text', st.session_state.extracted_text)
                
                with st.spinner("🎵 Creating audio..."):
                    audio_bytes = self.audio_gen.text_to_speech(text_to_speak)
                    
                    if audio_bytes:
                        st.session_state.audio_bytes = audio_bytes
                        st.success("✅ Audio generated successfully!")
        
        with col2:
            if st.button("🗑️ Clear All", use_container_width=True):
                st.session_state.extracted_text = ""
                st.session_state.audio_bytes = None
                st.rerun()
        
        # Audio player
        if st.session_state.audio_bytes:
            st.markdown("<h4>▶️ Listen</h4>", unsafe_allow_html=True)
            st.audio(st.session_state.audio_bytes, format="audio/mp3")
            
            # Download button
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "⬇️ Download Audio (MP3)",
                    data=st.session_state.audio_bytes,
                    file_name="extracted_text.mp3",
                    mime="audio/mp3",
                    use_container_width=True
                )
            
            with col2:
                st.download_button(
                    "📝 Download Text (TXT)",
                    data=st.session_state.extracted_text,
                    file_name="extracted_text.txt",
                    mime="text/plain",
                    use_container_width=True
                )
    
    def render_help_section(self):
        """Render help and tips section"""
        with st.expander("❓ Help & Tips", expanded=False):
            st.markdown("""
            ### How to use VoiceRead:
            
            1. **Upload** an image containing text (PNG, JPG)
            2. **Review** the extracted text for accuracy
            3. **Generate** audio or download the text
            4. **Listen** to the audio or share it
            
            ### Tips for best results:
            - Use clear, well-lit images
            - Ensure text is horizontal and readable
            - Avoid blurry or low-resolution images
            - Crop images to show text only
            
            ### Keyboard Shortcuts:
            - Tab: Navigate between elements
            - Enter: Activate buttons
            - Space: Play/pause audio
            
            ### Privacy:
            - Images are processed locally
            - No data is stored on servers
            - Audio is generated on-demand
            """)
    
    def run(self):
        """Run the main application"""
        # Setup
        self.ui.configure_page()
        self.ui.apply_custom_css()
        
        # Header
        self.render_header()
        
        # Upload section
        uploaded_image = self.render_upload_section()
        
        if uploaded_image:
            # Preview
            self.render_image_preview(uploaded_image)
            
            # Process button
            if st.button("✨ Extract Text from Image", use_container_width=True, type="primary"):
                if self.process_image(uploaded_image):
                    st.rerun()
        
        # Results section
        self.render_results_section()
        
        # Help section
        self.render_help_section()


# Entry point
if __name__ == "__main__":
    app = VoiceReadApp()
    app.run()
