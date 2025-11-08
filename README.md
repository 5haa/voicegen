# Real-Time AI Voice Agent

A powerful real-time voice AI agent featuring natural conversation with Gemini AI and ultra-fast text-to-speech using Cloudflare Workers AI.

## Features

### AI Voice Agent (Main Feature)
- 🤖 Real-time voice conversation with Gemini AI
- 🎤 Instant voice recognition
- 🔊 Fast, natural-sounding voice responses
- ⚡ Smart interruption - AI stops when you speak
- 🧠 Concise, conversational AI responses (optimized for voice)
- 📦 Chunked audio generation for long responses (no delays!)
- 💬 Maintains conversation context
- 🌍 Multi-language support

### Text-to-Speech Generator
- 🎙️ Simple text-to-speech conversion
- 💰 Ultra-low cost ($0.0002 per minute)
- 🚀 Fast generation
- 🌐 Multiple languages (EN, ES, FR, ZH, JP, KR)

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Credentials**
   
   Create a `.env` file with the following:
   
   **Cloudflare (for Text-to-Speech):**
   - Get your Cloudflare Account ID from your [Cloudflare Dashboard](https://dash.cloudflare.com/)
   - Create an API Token with "Workers AI" permissions at https://dash.cloudflare.com/profile/api-tokens
   
   **Gemini AI (for Voice Assistant):**
   - Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
   
   Add to `.env`:
   ```
   CLOUDFLARE_ACCOUNT_ID=your_account_id
   CLOUDFLARE_API_TOKEN=your_api_token
   GEMINI_API_KEY=your_gemini_api_key
   ```

3. **Run the Application**
   ```bash
   python app.py
   ```

4. **Open in Browser**
   - **AI Voice Agent:** `http://localhost:5000` (Main app)
   - Text-to-Speech: `http://localhost:5000/tts`

## Usage

### AI Voice Agent (Main)
1. Click "Start Talking"
2. Speak naturally to the AI
3. The AI will:
   - Listen to your voice
   - Generate a concise, relevant response
   - Speak back to you
   - Automatically resume listening
4. **Smart Interruption:** Start speaking anytime to interrupt the AI
5. Continue natural back-and-forth conversation!

### Features:
- ⚡ **Fast responses** - Uses Gemini 2.0 Flash for instant replies
- 🎯 **Concise answers** - AI gives brief, conversational responses (1-3 sentences)
- 📦 **Chunked playback** - Long responses are split and played in parts (no waiting!)
- 🛑 **Voice interruption** - AI stops speaking when you start talking
- 🔄 **Continuous mode** - Keeps listening after each response

### Text-to-Speech Generator
1. Enter text to convert to speech
2. Select language
3. Generate and download audio

## Cost

Cloudflare Workers AI charges **$0.0002 per minute** of generated audio, making it extremely affordable for most use cases.

## API Endpoints

- `POST /api/generate-voice` - Generate voice from text
  - Body: `{ "text": "your text", "language": "EN" }`
  - Returns: Audio file (WAV)

- `POST /api/chat` - Chat with Gemini AI
  - Body: `{ "message": "your message", "history": [] }`
  - Returns: `{ "response": "AI response", "success": true }`

- `GET /api/health` - Health check
  - Returns: Server status and configuration info

## Tech Stack

- **Backend**: Python Flask
- **Text-to-Speech**: Cloudflare Workers AI (@cf/myshell-ai/melotts)
- **AI Model**: Google Gemini 2.0 Flash Exp (optimized for speed)
- **Speech Recognition**: Web Speech API (browser-based)
- **Frontend**: Vanilla JavaScript (no frameworks needed)

## How It Works

1. **Voice Input** → Web Speech API captures your speech
2. **AI Processing** → Gemini 2.0 Flash generates concise response (max 150 tokens)
3. **Text-to-Speech** → Cloudflare Workers AI converts to audio
4. **Chunking** → Long responses split into ~100 char chunks
5. **Streaming Playback** → Chunks play sequentially for faster response
6. **Auto-Resume** → Automatically listens for your next message

## Browser Compatibility

- **Voice Agent** requires Web Speech API support:
  - ✅ Google Chrome (Recommended)
  - ✅ Microsoft Edge
  - ✅ Safari (iOS/macOS)
  - ❌ Firefox (limited support)

## Supported Languages

- English (EN)
- Spanish (ES)
- French (FR)
- Chinese (ZH)
- Japanese (JP)
- Korean (KR)

## Deployment to Railway

### Prerequisites
1. A [Railway](https://railway.app/) account (free tier available)
2. Your API credentials ready:
   - Cloudflare Account ID and API Token
   - Gemini API Key

### Deployment Steps

1. **Create a New Project on Railway**
   - Go to [Railway](https://railway.app/)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository

2. **Add Environment Variables**
   
   In your Railway project settings, add these variables:
   ```
   CLOUDFLARE_ACCOUNT_ID=your_account_id
   CLOUDFLARE_API_TOKEN=your_api_token
   GEMINI_API_KEY=your_gemini_api_key
   FLASK_ENV=production
   ```

3. **Deploy**
   - Railway will automatically detect your Python app
   - It will install dependencies from `requirements.txt`
   - Start the app using the `Procfile`
   - Your app will be live at: `https://your-project.up.railway.app`

### Railway Configuration Details

- **Build**: Uses Nixpacks (auto-detected)
- **Start Command**: Defined in `Procfile` (`gunicorn app:app`)
- **Port**: Automatically assigned by Railway via `$PORT` environment variable
- **Restart Policy**: Automatic restart on failure (max 10 retries)

### Post-Deployment

1. Visit your Railway URL to access the AI Voice Agent
2. Add `/tts` to access the Text-to-Speech generator
3. Check `/api/health` to verify API configurations

### Troubleshooting

- **502 Bad Gateway**: Check if environment variables are set correctly
- **API Errors**: Verify your Cloudflare and Gemini API keys are valid
- **Build Fails**: Ensure `requirements.txt` has all dependencies


