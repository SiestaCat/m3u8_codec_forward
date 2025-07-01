from typing import List, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl, validator
from enum import Enum


class CodecType(str, Enum):
    # Modern video codecs
    H264 = "h264"
    H265 = "h265"
    AV1 = "av1"
    VP9 = "vp9"
    VP8 = "vp8"
    
    # Legacy video codecs
    MPEG4 = "mpeg4"
    MPEG2 = "mpeg2"
    MPEG1 = "mpeg1"
    H263 = "h263"
    SORENSON_SPARK = "sorenson_spark"
    VP6 = "vp6"
    VC1 = "vc1"
    THEORA = "theora"
    REALVIDEO = "realvideo"
    CINEPAK = "cinepak"
    INDEO = "indeo"
    MSVIDEO1 = "msvideo1"


class AudioCodec(str, Enum):
    # Modern audio codecs
    AAC_LC = "aac_lc"
    HE_AAC = "he_aac"
    XHE_AAC = "xhe_aac"
    AC3 = "ac3"
    EAC3 = "eac3"
    MP3 = "mp3"
    OPUS = "opus"
    VORBIS = "vorbis"
    
    # Legacy audio codecs
    MP2 = "mp2"
    MP1 = "mp1"
    WMA1 = "wma1"
    WMA2 = "wma2"
    REALAUDIO = "realaudio"
    
    # Backwards compatibility
    AAC = "aac_lc"  # Alias for AAC_LC


class ContainerFormat(str, Enum):
    # Modern containers
    TS = "ts"
    FMP4 = "fmp4"
    MP4 = "mp4"
    MKV = "mkv"
    WEBM = "webm"
    
    # Legacy containers
    MOV = "mov"
    MPEG_PS = "mpeg_ps"
    FLV = "flv"
    AVI = "avi"
    ASF = "asf"
    RM = "rm"
    RMVB = "rmvb"


class Resolution(BaseModel):
    width: int
    height: int
    
    @validator('width', 'height')
    def validate_positive(cls, v):
        if v <= 0:
            raise ValueError('Width and height must be positive')
        return v
    
    def __str__(self):
        return f"{self.width}x{self.height}"


class StreamVariant(BaseModel):
    codec: CodecType
    audio_codec: AudioCodec
    resolution: Resolution
    bitrate: int
    framerate: Optional[float] = None
    container: ContainerFormat = ContainerFormat.TS
    
    @property
    def variant_name(self) -> str:
        return f"{self.codec.value}_{self.resolution}_{self.bitrate}k_{self.container.value}"


class StreamInfo(BaseModel):
    url: HttpUrl
    duration: Optional[float] = None
    segments: List[str] = []
    variants: List[Dict[str, Any]] = []
    
    
class TranscodingConfig(BaseModel):
    input_url: HttpUrl
    output_variants: List[StreamVariant]
    output_port: int = 80
    output_host: str = "localhost"