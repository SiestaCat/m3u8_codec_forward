A continuación tienes una tabla completa con códecs de vídeo y audio, así como formatos de contenedor (incluyendo opciones legacy/antiguas), agrupados por categoría. Cada fila indica el identificador (típicamente utilizado en playlists HLS), el formato de contenedor o extensión más habitual, y su estado (moderno o legacy).

Antes de la tabla, un breve resumen de los hallazgos:

Apple define en su especificación de HLS los códecs de vídeo modernos H.264/AVC, H.265/HEVC y AV1, y los contenedores fragmentados TS y fMP4 para segmentos ([developer.apple.com][1]). Wowza y AWS confirman soporte de audio como AAC‑LC, HE‑AAC, xHE‑AAC, AC‑3, E‑AC‑3 y MP3 dentro de TS o fMP4 ([wowza.com][2], [docs.aws.amazon.com][3]). Para entornos legacy, el contenedor TS o incluso MPEG Program Stream puede alojar códecs como MPEG‑1, MPEG‑2, H.263, DivX/Xvid, Sorenson Spark, VP6, VC‑1 o RealVideo ([en.wikipedia.org][4], [en.wikipedia.org][5]).

## Tabla de códecs y formatos

| Categoría      | Elemento                     | Identificador / Extensión | Contenedor / Formato          | Estado  |
| -------------- | ---------------------------- | ------------------------- | ----------------------------- | ------- |
| **Vídeo**      | H.264 / AVC                  | `avc1.*`                  | TS, fMP4                      | Moderno |
| **Vídeo**      | H.265 / HEVC                 | `hvc1.*`, `hev1.*`        | TS (legacy en iOS), fMP4      | Moderno |
| **Vídeo**      | AV1                          | `av01.*`                  | fMP4                          | Moderno |
| **Vídeo**      | VP9                          | `vp09.*`                  | MKV, WebM, fMP4 (CMAF)        | Moderno |
| **Vídeo**      | VP8                          | `vp08.*`                  | WebM, MKV, TS/MP4 con plugins | Moderno |
| **Vídeo**      | MPEG‑4 Visual (DivX, XviD)   | `mpeg4` / `mp4v`          | PS (`.mpg`), TS, MP4, AVI     | Legacy  |
| **Vídeo**      | MPEG‑2 Video                 | `mpeg2video`              | TS, PS (`.mpg`), AVI          | Legacy  |
| **Vídeo**      | MPEG‑1 Video                 | `mpeg1video`              | PS (`.mpg`), TS               | Legacy  |
| **Vídeo**      | H.263 (incl. Sorenson Spark) | `h263` / `s263`           | FLV, PS, AVI                  | Legacy  |
| **Vídeo**      | Sorenson Spark               | `svq3`                    | FLV, MOV                      | Legacy  |
| **Vídeo**      | VP6                          | `vp06`                    | FLV                           | Legacy  |
| **Vídeo**      | VC‑1                         | `vc1`                     | ASF, MP4, AVI                 | Legacy  |
| **Vídeo**      | Theora                       | `theora`                  | Ogg (`.ogv`), MKV             | Legacy  |
| **Vídeo**      | RealVideo (RV10–RV40)        | `rv10..rv40`              | RM / RMVB                     | Legacy  |
| **Vídeo**      | Cinepak, Indeo, MSV1         | `cinepak`, `msvideo1`     | AVI                           | Legacy  |
| **Audio**      | AAC‑LC                       | `mp4a.40.2`               | TS, fMP4, MP4                 | Moderno |
| **Audio**      | HE‑AAC (AAC+)                | `mp4a.40.5`               | TS, fMP4                      | Moderno |
| **Audio**      | xHE‑AAC                      | `mp4a.40.5`+ext           | TS, fMP4                      | Moderno |
| **Audio**      | Dolby Digital (AC‑3)         | `ac-3`                    | TS, fMP4, MP4                 | Moderno |
| **Audio**      | Dolby Digital Plus (E‑AC‑3)  | `ec-3`                    | TS, fMP4, MP4                 | Moderno |
| **Audio**      | MP3                          | `mp3`                     | TS, FLV, MP3                  | Moderno |
| **Audio**      | MP2                          | `mp2`                     | PS, TS                        | Legacy  |
| **Audio**      | MP1                          | `mp1`                     | PS, TS                        | Legacy  |
| **Audio**      | Opus                         | `opus`                    | WebM, MKV, Ogg                | Moderno |
| **Audio**      | Vorbis                       | `vorbis`                  | WebM, Ogg                     | Moderno |
| **Audio**      | WMA                          | `wma1`, `wma2`            | ASF, AVI                      | Legacy  |
| **Audio**      | RealAudio                    | `.ra`, `.rm`              | RM                            | Legacy  |
| **Contenedor** | MPEG‑2 TS                    | `.ts`                     | —                             | Ambos   |
| **Contenedor** | Fragmented MP4 (fMP4)        | `.m4s` / `.mp4`           | —                             | Moderno |
| **Contenedor** | MP4                          | `.mp4`                    | —                             | Moderno |
| **Contenedor** | MOV                          | `.mov`                    | —                             | Legacy  |
| **Contenedor** | MPEG Program Stream          | `.mpg`                    | —                             | Legacy  |
| **Contenedor** | MKV                          | `.mkv`                    | —                             | Moderno |
| **Contenedor** | FLV                          | `.flv`                    | —                             | Legacy  |
| **Contenedor** | AVI                          | `.avi`                    | —                             | Legacy  |
| **Contenedor** | ASF                          | `.asf`, `.wmv`            | —                             | Legacy  |
| **Contenedor** | WebM                         | `.webm`                   | —                             | Moderno |
| **Contenedor** | RM / RMVB                    | `.rm`, `.rmvb`            | —                             | Legacy  |

---

**Referencias de la tabla:**

* **H.264/AVC, H.265/HEVC, AV1:** ([developer.apple.com][1]), ([en.wikipedia.org][4])
* **VP8, VP9:** ([wowza.com][2]), ([learn.microsoft.com][6])
* **MPEG‑4 Visual (DivX/Xvid), MPEG‑2, MPEG‑1, H.263, Cinepak, Indeo, MSV1:** ([en.wikipedia.org][5]), ([en.wikipedia.org][4])
* **Sorenson Spark, VP6:** ([wowza.com][2])
* **VC‑1:** ([learn.microsoft.com][6])
* **Theora:** ([en.wikipedia.org][7])
* **RealVideo:** ([en.wikipedia.org][8])
* **Audio (AAC‑LC, HE‑AAC, xHE‑AAC, AC‑3, E‑AC‑3, MP3):** ([wowza.com][2])
* **MP2, MP1, AC‑3, E‑AC‑3, MP3:** ([en.wikipedia.org][4])
* **Opus, Vorbis, WebM:** ([en.wikipedia.org][9])
* **RealAudio:** ([en.wikipedia.org][10])
* **Contenedores TS, fMP4:** ([developer.apple.com][1]), ([en.wikipedia.org][11])
* **MP4, SMIL, HLS ingest/output:** ([docs.aws.amazon.com][3])
* **Formatos FLV, AVI, ASF:** ([microfocus.com][12])

[1]: https://developer.apple.com/documentation/http-live-streaming/hls-authoring-specification-for-apple-devices?utm_source=chatgpt.com "HTTP Live Streaming (HLS) authoring specification for Apple devices"
[2]: https://www.wowza.com/docs/understanding-protocols-and-formats-supported-by-wowza-streaming-engine?utm_source=chatgpt.com "Understanding protocols and formats - Wowza"
[3]: https://docs.aws.amazon.com/mediapackage/latest/ug/supported-inputs-vod.html?utm_source=chatgpt.com "VOD supported codecs and input types - AWS Documentation"
[4]: https://en.wikipedia.org/wiki/Comparison_of_video_container_formats?utm_source=chatgpt.com "Comparison of video container formats"
[5]: https://en.wikipedia.org/wiki/List_of_codecs?utm_source=chatgpt.com "List of codecs - Wikipedia"
[6]: https://learn.microsoft.com/en-us/windows/uwp/audio-video-camera/supported-codecs?utm_source=chatgpt.com "Supported codecs - UWP applications - Learn Microsoft"
[7]: https://en.wikipedia.org/wiki/Theora?utm_source=chatgpt.com "Theora"
[8]: https://en.wikipedia.org/wiki/RealVideo?utm_source=chatgpt.com "RealVideo - Wikipedia"
[9]: https://en.wikipedia.org/wiki/WebM?utm_source=chatgpt.com "WebM"
[10]: https://en.wikipedia.org/wiki/RealAudio?utm_source=chatgpt.com "RealAudio - Wikipedia"
[11]: https://en.wikipedia.org/wiki/MPEG_transport_stream?utm_source=chatgpt.com "MPEG transport stream - Wikipedia"
[12]: https://www.microfocus.com/documentation/idol/IDOL_24_3/MediaServer_24.3_Documentation/Help/Content/Operations/Ingest/VideoSupportedFormats.htm?utm_source=chatgpt.com "Supported Audio and Video Codecs and Formats - OpenText"
