"""Provider-agnostic voice facade for API and application integrations."""

from __future__ import annotations

from typing import BinaryIO

from core import settings
from voice.stt import SpeechToText
from voice.tts import TextToSpeech


class VoiceManager:
    def __init__(self, stt: SpeechToText | None = None, tts: TextToSpeech | None = None):
        self.stt, self.tts = stt, tts

    @classmethod
    def from_settings(cls) -> VoiceManager:
        stt = (
            SpeechToText(provider=settings.VOICE_STT_PROVIDER)
            if settings.VOICE_STT_PROVIDER
            else None
        )
        tts = (
            TextToSpeech(provider=settings.VOICE_TTS_PROVIDER)
            if settings.VOICE_TTS_PROVIDER
            else None
        )
        return cls(stt, tts)

    def transcribe(self, audio: BinaryIO) -> str:
        if not self.stt:
            raise RuntimeError("Speech-to-text is not configured")
        return self.stt.transcribe(audio)

    def synthesize(self, text: str) -> tuple[bytes, str]:
        if not self.tts:
            raise RuntimeError("Text-to-speech is not configured")
        return self.tts.generate(text) or b"", self.tts.get_format()
