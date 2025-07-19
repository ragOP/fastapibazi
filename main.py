from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
import re
from typing import Optional, List, Dict, Any

app = FastAPI(title="YouTube Transcript API", description="FastAPI backend for fetching YouTube transcripts")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TranscriptRequest(BaseModel):
    url: str
    lang: Optional[str] = "en"

class TranscriptResponse(BaseModel):
    transcript: str
    raw: List[Dict[str, Any]]
    segmentCount: int
    videoId: str
    language: str
    requestedLanguage: str
    attemptedMethods: List[str]

def extract_video_id(url: str) -> Optional[str]:
    """Extract video ID from YouTube URL"""
    try:
        parsed = urlparse(url)
        
        # Handle youtu.be format
        if parsed.hostname == 'youtu.be':
            return parsed.path[1:]  # Remove leading slash
        
        # Handle youtube.com format
        if 'youtube.com' in parsed.hostname:
            query_params = parse_qs(parsed.query)
            return query_params.get('v', [None])[0]
        
        # Handle direct video ID
        if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
            return url
            
    except Exception as e:
        print(f"Error parsing URL: {e}")
        
    return None

@app.post("/get_transcript", response_model=TranscriptResponse)
async def get_transcript(request: TranscriptRequest):
    """Fetch YouTube transcript with multiple fallback methods"""
    
    video_id = extract_video_id(request.url)
    
    print("=== TRANSCRIPT REQUEST ===")
    print(f"URL: {request.url}")
    print(f"Video ID: {video_id}")
    print(f"Requested Language: {request.lang}")
    
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")
    
    transcript_data = None
    actual_language = request.lang
    attempted_methods = []
    
    try:
        # Method 1: Try with specific language
        try:
            print(f"Method 1: Trying with specific language: {request.lang}")
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = transcript_list.find_transcript([request.lang])
            transcript_data = transcript.fetch()
            attempted_methods.append(f"{request.lang} (success)")
            print("✅ Method 1 successful")
            print(f"Raw transcript data length: {len(transcript_data)}")
            
        except Exception as lang_error:
            attempted_methods.append(f"{request.lang} (failed: {str(lang_error)})")
            print(f"❌ Method 1 failed: {lang_error}")
            
            # Method 2: Try to get any available transcript
            try:
                print("Method 2: Trying to get any available transcript")
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                
                # Get all available transcripts
                available_transcripts = list(transcript_list)
                if available_transcripts:
                    # Try manually created transcripts first
                    manual_transcripts = [t for t in available_transcripts if not t.is_generated]
                    if manual_transcripts:
                        transcript = manual_transcripts[0]
                    else:
                        transcript = available_transcripts[0]
                    
                    transcript_data = transcript.fetch()
                    actual_language = transcript.language_code
                    attempted_methods.append(f"{actual_language} (success)")
                    print(f"✅ Method 2 successful with language: {actual_language}")
                    print(f"Raw transcript data length: {len(transcript_data)}")
                    
                else:
                    raise Exception("No transcripts available")
                    
            except Exception as fallback_error:
                attempted_methods.append(f"auto-detect (failed: {str(fallback_error)})")
                print(f"❌ Method 2 failed: {fallback_error}")
                
                # Method 3: Try common languages
                common_languages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh', 'hi', 'ar']
                for test_lang in common_languages:
                    if test_lang == request.lang:
                        continue  # Already tried this
                    
                    try:
                        print(f"Method 3: Trying language: {test_lang}")
                        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                        transcript = transcript_list.find_transcript([test_lang])
                        transcript_data = transcript.fetch()
                        actual_language = test_lang
                        attempted_methods.append(f"{test_lang} (success)")
                        print(f"✅ Method 3 successful with language: {test_lang}")
                        break
                        
                    except Exception as test_error:
                        attempted_methods.append(f"{test_lang} (failed)")
                        print(f"❌ Language {test_lang} failed: {test_error}")
                
                if not transcript_data:
                    raise Exception(f"All methods failed. Attempted: {', '.join(attempted_methods)}")
        
        print(f"Final attempt methods: {attempted_methods}")
        print(f"Transcript fetched successfully, segments: {len(transcript_data) if transcript_data else 0}")
        
        # DEBUG: Final transcript data check
        print("=== FINAL TRANSCRIPT DATA CHECK ===")
        print(f"transcript_data type: {type(transcript_data)}")
        print(f"transcript_data is list: {isinstance(transcript_data, list)}")
        print(f"transcript_data length: {len(transcript_data) if transcript_data else 0}")
        print(f"transcript_data sample: {transcript_data[:2] if transcript_data else []}")
        
        if not transcript_data or len(transcript_data) == 0:
            raise HTTPException(
                status_code=404, 
                detail={
                    "error": "No transcript found for this video",
                    "details": "No transcript segments available",
                    "videoId": video_id,
                    "attemptedMethods": attempted_methods
                }
            )
        
        # Extract text from transcript items and combine
        full_text = ' '.join([item.text for item in transcript_data])
        
        print("Transcript processed successfully:")
        print(f"- Length: {len(full_text)} characters")
        print(f"- Segments: {len(transcript_data)}")
        print(f"- Language used: {actual_language}")
        print(f"- First 100 chars: {full_text[:100]}...")
        
        # Convert transcript objects to dictionaries for JSON response
        raw_data = [
            {
                "text": item.text,
                "start": item.start,
                "duration": item.duration
            }
            for item in transcript_data
        ]
        
        return TranscriptResponse(
            transcript=full_text,
            raw=raw_data,
            segmentCount=len(transcript_data),
            videoId=video_id,
            language=actual_language,
            requestedLanguage=request.lang,
            attemptedMethods=attempted_methods
        )
        
    except HTTPException:
        raise
    except Exception as error:
        print("=== TRANSCRIPT ERROR ===")
        print(f"Error type: {type(error).__name__}")
        print(f"Error message: {str(error)}")
        print(f"Full error: {error}")
        
        # Handle specific error types
        if "Could not retrieve a transcript" in str(error):
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "No transcript available for this video",
                    "details": "This video does not have captions/subtitles available",
                    "videoId": video_id
                }
            )
        
        if "TranscriptsDisabled" in str(error):
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Transcripts are disabled for this video",
                    "details": "The video owner has disabled captions/subtitles",
                    "videoId": video_id
                }
            )
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to fetch transcript",
                "details": str(error),
                "videoId": video_id,
                "errorType": type(error).__name__
            }
        )

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "YouTube Transcript API is running"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "youtube-transcript-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 