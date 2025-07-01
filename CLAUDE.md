# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a dockerized Python library for M3U8 codec forwarding. The system takes an input M3U8 stream and generates multiple output streams with different codecs and formats.

**Core Functionality:**
- Input: Single M3U8 stream URL (e.g., `http://example.com/m3u8`)
- Output: Multiple M3U8 endpoints with different codecs/formats:
  - `http://localhost/codec1.m3u8`
  - `http://localhost/codec2.m3u8` 
  - `http://localhost/format1.m3u8`
  - etc.

## Architecture

The system likely consists of:
- M3U8 parser and segment downloader
- Multiple transcoding pipelines for different codecs/formats
- HTTP server to serve the transcoded streams
- Docker containerization for deployment

## Development Commands

⚠️ **All commands MUST be executed through Docker containers.**

### Docker Commands (Primary)
```bash
# Build and run with docker-compose (RECOMMENDED)
docker-compose up --build

# Build individual image
docker build -t m3u8-codec-forward .

# Run individual container
docker run -p 8080:80 m3u8-codec-forward

# Run with custom configuration
docker run -p 8080:80 -v $(pwd)/config:/app/config m3u8-codec-forward --config /app/config/config.json

# Interactive development shell
docker run -it --entrypoint /bin/bash m3u8-codec-forward
```

### Testing Commands (Docker)
```bash
# Run all tests in Docker
docker run --rm m3u8-codec-forward pytest

# Run unit tests only (fast)
docker run --rm m3u8-codec-forward pytest tests/test_*.py -k "not functional and not vlc and not slow"

# Run functional tests (requires network)
docker run --rm m3u8-codec-forward pytest tests/test_functional.py

# Run VLC-based tests (requires VLC player)
docker run --rm m3u8-codec-forward pytest tests/test_vlc_functional.py -v

# Run VLC tests with specific markers
docker run --rm m3u8-codec-forward pytest -m "vlc" -v
docker run --rm m3u8-codec-forward pytest -m "vlc and not slow" -v

# Run with coverage
docker run --rm m3u8-codec-forward pytest --cov=m3u8_codec_forward tests/

# Interactive test session
docker run --rm -it m3u8-codec-forward pytest -v

# Test specific VLC functionality
docker run --rm m3u8-codec-forward pytest tests/test_vlc_functional.py::TestVLCIntegration::test_vlc_apple_stream_playback -v -s
```

### Development Inside Container
```bash
# Enter development container
docker run -it --entrypoint /bin/bash m3u8-codec-forward

# Inside container - install in development mode
pip install -e .

# Inside container - run server directly
python -m m3u8_codec_forward.main --host 0.0.0.0 --port 80

# Inside container - run tests
pytest tests/

# Inside container - test VLC integration
vlc --version
vlc --intf dummy --play-and-exit "https://devstreaming-cdn.apple.com/videos/streaming/examples/img_bipbop_adv_example_fmp4/master.m3u8"

# Inside container - run VLC tests
pytest tests/test_vlc_functional.py -v -s

# Inside container - linting
flake8 src/
black src/
mypy src/
```

### Local Development (NOT RECOMMENDED)
```bash
# Only use if you have FFmpeg with all codecs installed locally
pip install -r requirements.txt
pip install -e .
python -m m3u8_codec_forward.main
```

## Architecture Overview

The system consists of four main components:

1. **M3U8Parser** (`src/m3u8_codec_forward/parser.py`): Parses master and media playlists, extracts variants and segments
2. **TranscodingEngine** (`src/m3u8_codec_forward/transcoder.py`): Manages FFmpeg processes for real-time transcoding
3. **FastAPI Server** (`src/m3u8_codec_forward/server.py`): REST API endpoints and serves transcoded content
4. **ConfigManager** (`src/m3u8_codec_forward/config.py`): Handles configuration and preset management

### Key Models (`src/m3u8_codec_forward/models.py`)
- `StreamVariant`: Defines codec, resolution, bitrate configuration
- `TranscodingConfig`: Complete transcoding job configuration
- `StreamInfo`: Parsed M3U8 playlist information

### Supported Codecs

**Modern Video Codecs:**
- H.264/AVC, H.265/HEVC, AV1, VP9, VP8

**Legacy Video Codecs:**
- MPEG-4, MPEG-2, MPEG-1, H.263, Sorenson Spark, VP6, VC-1, Theora, RealVideo, Cinepak, Indeo, MSVideo1

**Modern Audio Codecs:**
- AAC-LC, HE-AAC, xHE-AAC, AC-3, E-AC-3, MP3, Opus, Vorbis

**Legacy Audio Codecs:**
- MP2, MP1, WMA1, WMA2, RealAudio

**Container Formats:**
- Modern: TS, fMP4, MP4, MKV, WebM
- Legacy: MOV, MPEG-PS, FLV, AVI, ASF, RM, RMVB

### Configuration Presets
- **standard**: H.264 variants with AAC-LC audio in TS containers
- **high_efficiency**: H.265 in fMP4 and VP9 in WebM containers  
- **multi_codec**: H.264/TS, H.265/fMP4, VP9/WebM, AV1/fMP4
- **legacy_support**: MPEG-4/AVI, H.263/FLV, VP8/WebM
- **modern_web**: VP9/WebM and AV1/fMP4 optimized for web
- **audio_focus**: Various audio codecs (AC-3, E-AC-3, HE-AAC)

### VLC-Based Testing

The application includes comprehensive VLC-based testing for M3U8 stream validation:

**VLC Test Types:**
- **Stream Playback Validation**: Test actual playback of generated M3U8 streams
- **Codec Verification**: Verify that streams use the correct video/audio codecs
- **Container Format Testing**: Validate proper container format usage (TS, fMP4, WebM)
- **Multi-stream Testing**: Concurrent validation of multiple stream variants
- **Stream Analysis**: Detailed inspection of stream properties and metadata

**VLC Testing Commands:**
```bash
# Test VLC integration
docker run --rm m3u8-codec-forward pytest tests/test_vlc_functional.py

# Manual VLC testing inside container
docker run -it --entrypoint /bin/bash m3u8-codec-forward
vlc --intf dummy --play-and-exit "https://example.com/test.m3u8"

# VLC stream analysis
vlc --intf dummy --verbose 2 --run-time 5 "https://example.com/test.m3u8"
```

### Docker Execution Requirements

⚠️ **Important**: All development and execution must be done through Docker containers. The application requires FFmpeg with extensive codec support that may not be available on all host systems.

**Why Docker is Required:**
- FFmpeg with all codec libraries (libx264, libx265, libvpx, libaom-av1, etc.)
- VLC player for comprehensive M3U8 stream testing and validation
- Consistent environment across different platforms
- Proper handling of legacy codec dependencies
- Isolated runtime environment for transcoding processes
- Headless VLC testing capabilities for CI/CD pipelines

### Current Test Status

**Test Results (96% success rate):**
- ✅ **45/47 tests passing**
- ✅ **All VLC-based stream validation tests passing**
- ✅ **All model, parser, config, and integration tests passing**
- ❌ **2 API tests failing** (TestClient compatibility issue, not affecting functionality)

**Port Configuration:**
- **Internal Container Port**: 80
- **External Host Port**: 8080 (mapped as `8080:80`)
- **API Access**: `http://localhost:8080/`

**Key Features:**
- **Bidirectional Codec Conversion**: Modern ↔ Legacy format conversion
- **Auto-Start Transcoding**: Access playlists directly with `?input_url` parameter
- **VLC-Based Stream Validation**: Comprehensive stream testing and analysis