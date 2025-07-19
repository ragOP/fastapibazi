# YouTube Transcript API - Python/FastAPI Backend

A Python FastAPI backend for fetching YouTube video transcripts with multiple language fallback methods.

## Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the server:**
   ```bash
   python run.py
   ```

   Or alternatively:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

3. **The server will be available at:**
   - API: `http://localhost:8000`
   - API Documentation: `http://localhost:8000/docs`
   - Health Check: `http://localhost:8000/health`

## API Endpoints

### POST `/get_transcript`

Fetch a YouTube video transcript.

**Request Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "lang": "en"  // optional, defaults to "en"
}
```

**Response:**
```json
{
  "transcript": "Full transcript text...",
  "raw": [
    {
      "text": "Hello everyone",
      "start": 0.0,
      "duration": 2.5
    }
  ],
  "segmentCount": 150,
  "videoId": "VIDEO_ID",
  "language": "en",
  "requestedLanguage": "en",
  "attemptedMethods": ["en (success)"]
}
```

### GET `/health`

Health check endpoint.

## Features

- **Multiple fallback methods**: Tries requested language first, then auto-detection, then common languages
- **Robust error handling**: Provides detailed error messages for different failure scenarios
- **CORS enabled**: Works with frontend applications
- **Comprehensive logging**: Detailed logs for debugging
- **Structured responses**: Consistent JSON responses with metadata

## Error Handling

The API handles various error scenarios:

- **400**: Invalid YouTube URL
- **404**: No transcript available for the video
- **422**: Requested language not available (with available languages listed)
- **500**: Server error

## Supported URL Formats

- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- Direct video ID: `VIDEO_ID`

## Language Support

The API automatically tries multiple languages if the requested language is not available:

1. Requested language (e.g., "en")
2. Auto-detection (any available transcript)
3. Common languages: en, es, fr, de, it, pt, ru, ja, ko, zh, hi, ar 