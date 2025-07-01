from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import HttpUrl
from typing import Dict, Optional
import logging
from pathlib import Path
import asyncio
from contextlib import asynccontextmanager

from .models import TranscodingConfig, StreamVariant, CodecType, AudioCodec, Resolution, ContainerFormat
from .transcoder import TranscodingEngine

logger = logging.getLogger(__name__)

# Global state
transcoding_engine: Optional[TranscodingEngine] = None
active_streams: Dict[str, Dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global transcoding_engine
    transcoding_engine = TranscodingEngine()
    yield
    # Shutdown
    if transcoding_engine:
        await transcoding_engine.close()


app = FastAPI(title="M3U8 Codec Forward", version="0.1.0", lifespan=lifespan)


@app.post("/start-transcoding")
async def start_transcoding(
    input_url: HttpUrl,
    background_tasks: BackgroundTasks,
    output_host: str = "localhost",
    output_port: int = 80
):
    global transcoding_engine, active_streams
    
    if not transcoding_engine:
        raise HTTPException(status_code=500, detail="Transcoding engine not initialized")
    
    # Default output variants
    output_variants = [
        StreamVariant(
            codec=CodecType.H264,
            audio_codec=AudioCodec.AAC_LC,
            resolution=Resolution(width=1920, height=1080),
            bitrate=5000,
            framerate=30.0,
            container=ContainerFormat.TS
        ),
        StreamVariant(
            codec=CodecType.H264,
            audio_codec=AudioCodec.AAC_LC,
            resolution=Resolution(width=1280, height=720),
            bitrate=3000,
            framerate=30.0,
            container=ContainerFormat.TS
        ),
        StreamVariant(
            codec=CodecType.H265,
            audio_codec=AudioCodec.AAC_LC,
            resolution=Resolution(width=1920, height=1080),
            bitrate=3000,
            framerate=30.0,
            container=ContainerFormat.FMP4
        ),
        StreamVariant(
            codec=CodecType.VP9,
            audio_codec=AudioCodec.OPUS,
            resolution=Resolution(width=1280, height=720),
            bitrate=2500,
            framerate=30.0,
            container=ContainerFormat.WEBM
        )
    ]
    
    config = TranscodingConfig(
        input_url=input_url,
        output_variants=output_variants,
        output_host=output_host,
        output_port=output_port
    )
    
    try:
        variant_urls = await transcoding_engine.start_transcoding(config)
        
        stream_id = str(input_url)
        active_streams[stream_id] = {
            "input_url": str(input_url),
            "variants": variant_urls,
            "config": config.dict()
        }
        
        return {
            "message": "Transcoding started successfully",
            "stream_id": stream_id,
            "variants": variant_urls
        }
        
    except Exception as e:
        logger.error(f"Failed to start transcoding: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start transcoding: {str(e)}")


@app.get("/streams")
async def list_active_streams():
    return {
        "active_streams": active_streams,
        "total_streams": len(active_streams)
    }


@app.get("/uris")
async def get_all_uris():
    """Return all available stream URIs from active streams."""
    all_uris = []
    
    for stream_id, stream_data in active_streams.items():
        variants = stream_data.get("variants", {})
        for variant_name, variant_uri in variants.items():
            all_uris.append({
                "stream_id": stream_id,
                "variant_name": variant_name,
                "uri": variant_uri
            })
    
    return {
        "total_uris": len(all_uris),
        "uris": all_uris
    }


@app.delete("/streams/{stream_id}")
async def stop_stream(stream_id: str):
    global transcoding_engine, active_streams
    
    if stream_id not in active_streams:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    try:
        await transcoding_engine.stop_transcoding()
        del active_streams[stream_id]
        
        return {"message": f"Stream {stream_id} stopped successfully"}
        
    except Exception as e:
        logger.error(f"Failed to stop stream: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop stream: {str(e)}")


@app.get("/{variant_name}.m3u8")
async def serve_playlist(variant_name: str, input_url: HttpUrl = None):
    global transcoding_engine, active_streams
    
    if not transcoding_engine:
        raise HTTPException(status_code=500, detail="Transcoding engine not initialized")
    
    playlist_path = transcoding_engine.working_dir / f"{variant_name}.m3u8"
    
    if not playlist_path.exists():
        # If no active transcoding and input_url provided, start transcoding automatically
        if input_url and not active_streams:
            try:
                # Use default variants for auto-start
                output_variants = [
                    StreamVariant(
                        codec=CodecType.H264,
                        audio_codec=AudioCodec.AAC_LC,
                        resolution=Resolution(width=1920, height=1080),
                        bitrate=5000,
                        framerate=30.0,
                        container=ContainerFormat.TS
                    ),
                    StreamVariant(
                        codec=CodecType.H264,
                        audio_codec=AudioCodec.AAC_LC,
                        resolution=Resolution(width=1280, height=720),
                        bitrate=3000,
                        framerate=30.0,
                        container=ContainerFormat.TS
                    ),
                    StreamVariant(
                        codec=CodecType.H265,
                        audio_codec=AudioCodec.AAC_LC,
                        resolution=Resolution(width=1920, height=1080),
                        bitrate=3000,
                        framerate=30.0,
                        container=ContainerFormat.FMP4
                    ),
                    StreamVariant(
                        codec=CodecType.VP9,
                        audio_codec=AudioCodec.OPUS,
                        resolution=Resolution(width=1280, height=720),
                        bitrate=2500,
                        framerate=30.0,
                        container=ContainerFormat.WEBM
                    )
                ]
                
                config = TranscodingConfig(
                    input_url=input_url,
                    output_variants=output_variants,
                    output_host="localhost",
                    output_port=80
                )
                
                variant_urls = await transcoding_engine.start_transcoding(config)
                
                stream_id = str(input_url)
                active_streams[stream_id] = {
                    "input_url": str(input_url),
                    "variants": variant_urls,
                    "config": config.model_dump()
                }
                
                # Wait a moment for the playlist file to be created
                import asyncio
                await asyncio.sleep(1)
                
                # Check again if file exists
                if playlist_path.exists():
                    return FileResponse(
                        path=str(playlist_path),
                        media_type="application/vnd.apple.mpegurl",
                        headers={"Cache-Control": "no-cache"}
                    )
                    
            except Exception as e:
                logger.error(f"Failed to auto-start transcoding: {e}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"Failed to auto-start transcoding for {variant_name}: {str(e)}"
                )
        
        # Provide informative error message
        if not active_streams:
            raise HTTPException(
                status_code=404, 
                detail=f"Playlist '{variant_name}.m3u8' not found. No active transcoding streams. Start transcoding first with POST /start-transcoding or provide ?input_url=<stream_url> parameter."
            )
        else:
            raise HTTPException(
                status_code=404, 
                detail=f"Playlist '{variant_name}.m3u8' not found. Available variants: {list(active_streams.keys())}"
            )
    
    return FileResponse(
        path=str(playlist_path),
        media_type="application/vnd.apple.mpegurl",
        headers={"Cache-Control": "no-cache"}
    )


@app.get("/{segment_name}")
async def serve_segment(segment_name: str):
    global transcoding_engine
    
    if not transcoding_engine:
        raise HTTPException(status_code=500, detail="Transcoding engine not initialized")
    
    segment_path = transcoding_engine.working_dir / segment_name
    
    if not segment_path.exists():
        raise HTTPException(status_code=404, detail="Segment not found")
    
    return FileResponse(
        path=str(segment_path),
        media_type="video/mp2t"
    )


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "m3u8-codec-forward"}


@app.get("/")
async def root():
    return {
        "service": "M3U8 Codec Forward",
        "version": "0.1.0",
        "endpoints": {
            "start_transcoding": "POST /start-transcoding",
            "list_streams": "GET /streams", 
            "get_all_uris": "GET /uris",
            "stop_stream": "DELETE /streams/{stream_id}",
            "serve_playlist": "GET /{variant_name}.m3u8",
            "serve_segment": "GET /{segment_name}",
            "health": "GET /health"
        }
    }