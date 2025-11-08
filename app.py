import os
import re
import requests
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import io
import json
import base64
import google.generativeai as genai

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Cloudflare configuration
CLOUDFLARE_ACCOUNT_ID = os.getenv('CLOUDFLARE_ACCOUNT_ID')
CLOUDFLARE_API_TOKEN = os.getenv('CLOUDFLARE_API_TOKEN')
CLOUDFLARE_API_BASE = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run"
MODEL_NAME = "@cf/myshell-ai/melotts"

# Gemini AI configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


@app.route('/')
def index():
    """Serve the main voice assistant page"""
    return render_template('assistant.html')


@app.route('/tts')
def tts_generator():
    """Serve the text-to-speech generator page"""
    return render_template('index.html')


@app.route('/api/generate-voice', methods=['POST'])
def generate_voice():
    """Generate voice from text using Cloudflare Workers AI"""
    
    # Check if credentials are configured
    if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
        return jsonify({
            'error': 'Cloudflare credentials not configured. Please check your .env file.'
        }), 500
    
    # Get request data
    data = request.get_json()
    text = data.get('text', '')
    language = data.get('language', 'EN')
    
    if not text:
        return jsonify({'error': 'Text is required'}), 400
    
    # Prepare the request to Cloudflare Workers AI
    headers = {
        'Authorization': f'Bearer {CLOUDFLARE_API_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    # Map language codes - Cloudflare uses lowercase 2-letter codes
    lang_map = {
        'EN': 'en',
        'ES': 'es',
        'FR': 'fr',
        'ZH': 'zh',
        'JP': 'ja',
        'KR': 'ko'
    }
    
    payload = {
        'prompt': text,
        'lang': lang_map.get(language, 'en')
    }
    
    try:
        # Make request to Cloudflare Workers AI
        response = requests.post(
            f"{CLOUDFLARE_API_BASE}/{MODEL_NAME}",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            # Parse JSON response
            response_data = response.json()
            
            # Extract base64-encoded audio from the result
            if 'result' in response_data and 'audio' in response_data['result']:
                base64_audio = response_data['result']['audio']
                
                # Decode base64 to get the actual audio bytes
                audio_bytes = base64.b64decode(base64_audio)
                
                # Return the audio file (it's a WAV file)
                return send_file(
                    io.BytesIO(audio_bytes),
                    mimetype='audio/wav',
                    as_attachment=False,
                    download_name='generated_voice.wav'
                )
            else:
                return jsonify({'error': 'Invalid response format from API'}), 500
        else:
            error_message = f"Cloudflare API Error: {response.status_code}"
            try:
                error_data = response.json()
                error_message = error_data.get('errors', [{}])[0].get('message', error_message)
            except:
                pass
            
            return jsonify({'error': error_message}), response.status_code
            
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Request timed out. Please try again.'}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/api/voices', methods=['GET'])
def get_voices():
    """Get available voices and languages"""
    voices = {
        'languages': {
            'EN': 'English',
            'ES': 'Spanish',
            'FR': 'French',
            'ZH': 'Chinese',
            'JP': 'Japanese',
            'KR': 'Korean'
        },
        'speakers': {
            'EN': ['EN-Default', 'EN-US', 'EN-BR', 'EN-INDIA', 'EN-AU'],
            'ES': ['ES', 'ES-MX'],
            'FR': ['FR'],
            'ZH': ['ZH'],
            'JP': ['JP'],
            'KR': ['KR']
        }
    }
    return jsonify(voices)


@app.route('/api/generate-voice-chunked', methods=['POST'])
def generate_voice_chunked():
    """Generate voice in chunks for long text"""
    
    if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
        return jsonify({
            'error': 'Cloudflare credentials not configured.'
        }), 500
    
    data = request.get_json()
    text = data.get('text', '')
    language = data.get('language', 'EN')
    
    if not text:
        return jsonify({'error': 'Text is required'}), 400
    
    # Split text into sentences for chunking (split on sentence boundaries)
    # Include ellipsis as a sentence boundary for natural pauses
    sentences = re.split(r'(?<=[.!?])\s+|(?<=\.\.\.)\s+', text)
    
    # Group sentences into chunks (max ~400 chars per chunk for smoother delivery)
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        # Add sentence if it fits within chunk size
        if len(current_chunk) + len(sentence) < 400:
            current_chunk += sentence + " "
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    # If only one chunk, use regular endpoint
    if len(chunks) <= 1:
        return generate_voice()
    
    # Return chunks info for client-side processing
    return jsonify({
        'chunks': chunks,
        'total': len(chunks)
    })


def clean_text_for_tts(text):
    """Clean and optimize text for TTS voice generation"""
    # Remove markdown formatting
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Remove bold **text**
    text = re.sub(r'\*(.+?)\*', r'\1', text)  # Remove italic *text*
    text = re.sub(r'`(.+?)`', r'\1', text)  # Remove code `text`
    
    # Remove bullet points and list markers
    text = re.sub(r'^\s*[-*•]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    
    # Remove multiple spaces (but preserve periods for pauses)
    text = re.sub(r'[^\S.]+', ' ', text)
    
    # Ensure proper spacing after punctuation (but not for multiple dots)
    text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)
    
    # Normalize ellipsis patterns for TTS:
    # 9+ dots = extra long pause (keep as many dots for dramatic pause)
    # 3-8 dots = normalize to triple dots (regular ellipsis)
    # Preserve long pauses for vocabulary lists!
    text = re.sub(r'\.{9,}', '..............', text)  # 9+ dots = extra long pause
    text = re.sub(r'\.{3,8}', '...', text)  # 3-8 dots = regular ellipsis
    
    # Clean up other multiple punctuation marks
    text = re.sub(r'[!]{2,}', '!', text)  # Multiple exclamation marks to single
    text = re.sub(r'[?]{2,}', '?', text)  # Multiple question marks to single
    
    # Remove any remaining special characters that might confuse TTS
    text = re.sub(r'[#@$%^&*_+=\[\]{}|\\<>~]', '', text)
    
    # Clean up spacing around ellipsis
    text = re.sub(r'\s+\.', '.', text)  # Remove spaces before dots
    text = re.sub(r'\s{2,}', ' ', text)  # Multiple spaces to single
    
    return text.strip()


@app.route('/api/chat', methods=['POST'])
def chat_with_gemini():
    """Chat with Gemini AI"""
    
    # Check if Gemini is configured
    if not GEMINI_API_KEY:
        return jsonify({
            'error': 'Gemini API key not configured. Please check your .env file.'
        }), 500
    
    # Get request data
    data = request.get_json()
    message = data.get('message', '')
    conversation_history = data.get('history', [])
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    try:
        # Initialize Gemini model with system instructions for concise responses
        system_instruction = """You are a friendly and encouraging language tutor having a voice conversation with a student. 

IMPORTANT RULES:
- NEVER use special characters, bullet points, asterisks, or markdown formatting in your responses
- Speak naturally as if talking to someone face to face
- Keep responses conversational and brief, typically 2-3 sentences
- Be encouraging and supportive, celebrating progress
- Use simple, clear language appropriate for language learners
- Ask follow-up questions to keep the student engaged
- Provide gentle corrections and explanations when needed
- Adapt to the student's level and learning pace
- Make learning feel like a friendly conversation, not a lecture

VOICE PACING (CRITICAL for natural speech):
Your text will be converted to speech by a voice model. Use punctuation strategically to create natural pauses:
- Use commas for SHORT pauses (breathing points)
- Use periods for MEDIUM pauses (end of thoughts)
- Use "..." (ellipsis) for LONGER pauses (thinking, giving student time to process)
- Use "........." (many dots) for EXTRA LONG pauses (after vocabulary words, waiting for student response)

VOCABULARY WORD LISTS (VERY IMPORTANT):
When giving vocabulary words or lists, students need TIME to think and process each word:
- Add LONG pauses between each word using multiple dots: "........."
- Speak each word slowly and clearly
- Add brief context or encouragement between words
- Give students time to mentally process each word

GOOD Example (vocabulary list):
"Okay! Here's your first word... ubiquitous......... Second word... mellifluous......... Third word... ephemeral......... And last one... serendipity......... Take your time with each one!"

BAD Example (too fast):
"Okay, here are the words. Ubiquitous, mellifluous, ephemeral, serendipity. How did you do?"

GOOD Example (normal conversation):
"That's correct! The word ubiquitous means something that appears everywhere. It's a great word to learn... Do you want to try using it in a sentence?"

Remember: For word lists, add LONG pauses (..........) between words. For normal conversation, use shorter pauses (... or .)"""
        
        model = genai.GenerativeModel(
            'gemini-2.0-flash',  # Fast and stable model with better rate limits
            system_instruction=system_instruction
        )
        
        # Build conversation context with teaching mode detection
        prompt = message
        
        # Detect if user is asking for word lists or vocabulary practice
        teaching_mode_hint = ""
        if any(keyword in message.lower() for keyword in [
            'list of words', 'give me words', 'vocabulary words', 'practice words',
            'word list', 'some words', 'quiz me', 'test me'
        ]):
            teaching_mode_hint = "\n[TEACHING MODE: User wants vocabulary practice. Use LONG pauses (..........) between each word!]"
        
        if conversation_history:
            context = "\n".join([
                f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                for msg in conversation_history[-6:]  # Last 6 messages for context
            ])
            prompt = f"Previous conversation:\n{context}\n\nUser: {message}{teaching_mode_hint}"
        else:
            prompt = f"User: {message}{teaching_mode_hint}"
        
        # Generate response with temperature for natural conversation
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.8,  # Slightly higher for more natural, varied teaching responses
                max_output_tokens=250,  # Allow longer responses for teaching with proper pauses
            )
        )
        ai_response = response.text
        
        # Clean the response for optimal TTS voice generation
        ai_response = clean_text_for_tts(ai_response)
        
        return jsonify({
            'response': ai_response,
            'success': True
        })
        
    except Exception as e:
        return jsonify({'error': f'Gemini API error: {str(e)}'}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    is_configured = bool(CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN)
    gemini_configured = bool(GEMINI_API_KEY)
    return jsonify({
        'status': 'healthy',
        'configured': is_configured,
        'gemini_configured': gemini_configured
    })


if __name__ == '__main__':
    # Check if credentials are configured
    if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
        print("\n[!] WARNING: Cloudflare credentials not found!")
        print("Please copy .env.example to .env and add your credentials.\n")
    else:
        print("\n[OK] Cloudflare credentials found!")
        print(f"[*] Account ID: {CLOUDFLARE_ACCOUNT_ID[:8]}...")
        print(f"[*] API Token: {CLOUDFLARE_API_TOKEN[:8]}...\n")
    
    # Use PORT from environment variable (Railway/Heroku) or default to 5000 for local
    port = int(os.getenv('PORT', 5000))
    debug_mode = os.getenv('FLASK_ENV') != 'production'
    
    print("[*] Starting Real-Time Voice Generation Server...")
    print(f"[*] Running on port {port}\n")
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port)


