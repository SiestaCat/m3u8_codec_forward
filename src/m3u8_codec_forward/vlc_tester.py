"""VLC-based testing utilities for M3U8 streams."""

import asyncio
import subprocess
import tempfile
import time
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class VLCTester:
    """VLC-based M3U8 stream tester for validation and analysis."""
    
    def __init__(self, vlc_timeout: int = 30):
        self.vlc_timeout = vlc_timeout
        self.temp_dir = Path(tempfile.mkdtemp())
    
    async def test_stream_playback(self, stream_url: str, duration_seconds: int = 10) -> Dict[str, any]:
        """
        Test M3U8 stream playback using VLC.
        
        Args:
            stream_url: URL of the M3U8 stream to test
            duration_seconds: How long to test playback (seconds)
            
        Returns:
            Dict containing test results and stream information
        """
        result = {
            "stream_url": stream_url,
            "playback_success": False,
            "duration_tested": duration_seconds,
            "error": None,
            "stream_info": {},
            "vlc_output": ""
        }
        
        try:
            # Create temporary log file for VLC output
            log_file = self.temp_dir / f"vlc_test_{int(time.time())}.log"
            
            # VLC command for headless testing
            vlc_cmd = [
                "vlc",
                "--intf", "dummy",
                "--quiet",
                "--no-video",  # Audio only for testing to avoid display issues
                "--play-and-exit",
                "--run-time", str(duration_seconds),
                "--extraintf", "logger",
                "--logfile", str(log_file),
                stream_url
            ]
            
            logger.info(f"Testing stream with VLC: {stream_url}")
            
            # Run VLC process
            process = await asyncio.create_subprocess_exec(
                *vlc_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.temp_dir)
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=self.vlc_timeout
                )
                
                # Read VLC log file if it exists
                vlc_output = ""
                if log_file.exists():
                    vlc_output = log_file.read_text()
                
                result["vlc_output"] = vlc_output
                
                # Check for actual playback success - VLC might exit with 0 even on errors
                stderr_text = stderr.decode().lower()
                vlc_output_lower = vlc_output.lower()
                
                # Look for error indicators
                has_errors = any(error_term in stderr_text or error_term in vlc_output_lower 
                               for error_term in ['error', 'failed', 'cannot', 'unable', 'connection refused', 'not found'])
                
                # VLC returncode 0 AND no error indicators = success
                result["playback_success"] = process.returncode == 0 and not has_errors
                
                if process.returncode != 0 or has_errors:
                    error_msg = f"VLC exited with code {process.returncode}"
                    if stderr_text:
                        error_msg += f": {stderr.decode()}"
                    if has_errors and vlc_output:
                        error_msg += f" (VLC output contains errors)"
                    result["error"] = error_msg
                
                # Extract stream information from VLC output
                result["stream_info"] = self._parse_vlc_output(vlc_output)
                
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                result["error"] = f"VLC test timed out after {self.vlc_timeout} seconds"
                
        except Exception as e:
            result["error"] = f"VLC test failed: {str(e)}"
            logger.error(f"VLC test error for {stream_url}: {e}")
        
        return result
    
    def _parse_vlc_output(self, vlc_output: str) -> Dict[str, any]:
        """Parse VLC log output to extract stream information."""
        info = {
            "codec": None,
            "resolution": None,
            "bitrate": None,
            "fps": None,
            "audio_codec": None,
            "errors": []
        }
        
        if not vlc_output:
            return info
        
        lines = vlc_output.split('\n')
        for line in lines:
            line = line.strip().lower()
            
            # Extract codec information
            if 'codec:' in line:
                if 'video' in line:
                    if 'h264' in line or 'avc' in line:
                        info["codec"] = "h264"
                    elif 'h265' in line or 'hevc' in line:
                        info["codec"] = "h265"
                    elif 'vp9' in line:
                        info["codec"] = "vp9"
                    elif 'av1' in line:
                        info["codec"] = "av1"
                elif 'audio' in line:
                    if 'aac' in line:
                        info["audio_codec"] = "aac"
                    elif 'mp3' in line:
                        info["audio_codec"] = "mp3"
                    elif 'opus' in line:
                        info["audio_codec"] = "opus"
            
            # Extract resolution
            if 'resolution:' in line or ('x' in line and any(res in line for res in ['1920', '1280', '854', '640'])):
                parts = line.split()
                for part in parts:
                    if 'x' in part and any(char.isdigit() for char in part):
                        info["resolution"] = part
                        break
            
            # Extract frame rate
            if 'fps' in line or 'frame rate' in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.replace('.', '').isdigit() and (i+1 < len(parts) and 'fps' in parts[i+1]):
                        info["fps"] = float(part)
                        break
            
            # Capture errors
            if 'error' in line or 'failed' in line or 'cannot' in line:
                info["errors"].append(line)
        
        return info
    
    async def test_multiple_streams(self, stream_urls: List[str], duration_seconds: int = 10) -> Dict[str, Dict]:
        """Test multiple M3U8 streams concurrently."""
        logger.info(f"Testing {len(stream_urls)} streams with VLC")
        
        tasks = []
        for url in stream_urls:
            task = self.test_stream_playback(url, duration_seconds)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        stream_results = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                stream_results[stream_urls[i]] = {
                    "playback_success": False,
                    "error": str(result)
                }
            else:
                stream_results[stream_urls[i]] = result
        
        return stream_results
    
    async def validate_stream_variants(self, base_url: str, variants: List[str]) -> Dict[str, any]:
        """
        Validate multiple stream variants from a base URL.
        
        Args:
            base_url: Base URL (e.g., "http://localhost:8080")
            variants: List of variant names (e.g., ["h264_1080p_5000k_ts"])
            
        Returns:
            Validation results for all variants
        """
        stream_urls = [f"{base_url}/{variant}.m3u8" for variant in variants]
        results = await self.test_multiple_streams(stream_urls)
        
        # Add summary statistics
        total_streams = len(results)
        successful_streams = sum(1 for r in results.values() if r.get("playback_success", False))
        
        summary = {
            "total_streams": total_streams,
            "successful_streams": successful_streams,
            "success_rate": successful_streams / total_streams if total_streams > 0 else 0,
            "stream_results": results
        }
        
        return summary
    
    def cleanup(self):
        """Clean up temporary files."""
        try:
            import shutil
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            logger.warning(f"Failed to cleanup temp directory: {e}")


class VLCStreamAnalyzer:
    """VLC-based stream analyzer for detailed M3U8 inspection."""
    
    @staticmethod
    async def analyze_stream_details(stream_url: str) -> Dict[str, any]:
        """
        Analyze M3U8 stream using VLC's detailed inspection capabilities.
        
        Returns detailed codec, bitrate, and quality information.
        """
        result = {
            "stream_url": stream_url,
            "analysis_success": False,
            "details": {},
            "error": None
        }
        
        try:
            # Use VLC with verbose output for analysis
            vlc_cmd = [
                "vlc",
                "--intf", "dummy",
                "--verbose", "2",
                "--no-audio",
                "--no-video-output",
                "--run-time", "5",
                "--stop-time", "5",
                stream_url,
                "vlc://quit"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *vlc_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=30
            )
            
            # Parse the verbose output for detailed information
            output = stdout.decode() + stderr.decode()
            result["details"] = VLCStreamAnalyzer._parse_detailed_output(output)
            result["analysis_success"] = True
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"VLC analysis failed for {stream_url}: {e}")
        
        return result
    
    @staticmethod
    def _parse_detailed_output(output: str) -> Dict[str, any]:
        """Parse VLC verbose output for detailed stream information."""
        details = {
            "video_codec": None,
            "audio_codec": None,
            "container": None,
            "bitrate": None,
            "resolution": None,
            "fps": None,
            "duration": None,
            "segments_info": []
        }
        
        lines = output.split('\n')
        for line in lines:
            line_lower = line.lower()
            
            # Extract detailed codec information
            if 'using video decoder module' in line_lower:
                if 'h264' in line_lower:
                    details["video_codec"] = "H.264"
                elif 'hevc' in line_lower or 'h265' in line_lower:
                    details["video_codec"] = "H.265"
                elif 'vp9' in line_lower:
                    details["video_codec"] = "VP9"
                elif 'av1' in line_lower:
                    details["video_codec"] = "AV1"
            
            if 'using audio decoder module' in line_lower:
                if 'aac' in line_lower:
                    details["audio_codec"] = "AAC"
                elif 'mp3' in line_lower:
                    details["audio_codec"] = "MP3"
                elif 'opus' in line_lower:
                    details["audio_codec"] = "Opus"
            
            # Extract container format
            if 'using demux module' in line_lower:
                if 'ts' in line_lower:
                    details["container"] = "MPEG-TS"
                elif 'mp4' in line_lower:
                    details["container"] = "MP4"
                elif 'webm' in line_lower:
                    details["container"] = "WebM"
        
        return details