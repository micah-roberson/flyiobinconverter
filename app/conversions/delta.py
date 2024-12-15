from pydub import AudioSegment
import numpy as np
import io

def convert(audio: AudioSegment) -> AudioSegment:
    print("Processing Delta (0.5–4 Hz) conversion...")

    # Define parameters
    target_frequency = 2  # Target binaural beat frequency in Hz (within the delta range)
    base_frequency = 100  # Base tone frequency in Hz
    sample_rate = 44100  # Sample rate in Hz
    duration_ms = len(audio)  # Duration of the audio in milliseconds

    # Generate time array
    t = np.linspace(0, duration_ms / 1000, int(sample_rate * (duration_ms / 1000)), endpoint=False)

    # Generate left and right channel tones
    left_tone = np.sin(2 * np.pi * base_frequency * t)
    right_tone = np.sin(2 * np.pi * (base_frequency + target_frequency) * t)

    # Convert tones to AudioSegment
    left_channel = AudioSegment(
        (left_tone * 32767).astype(np.int16).tobytes(),
        frame_rate=sample_rate,
        sample_width=2,
        channels=1
    )
    right_channel = AudioSegment(
        (right_tone * 32767).astype(np.int16).tobytes(),
        frame_rate=sample_rate,
        sample_width=2,
        channels=1
    )

    # Combine tones into a stereo AudioSegment
    binaural_beat = AudioSegment.from_mono_audiosegments(left_channel, right_channel)

    # Overlay the binaural beat onto the original audio
    combined = audio.overlay(binaural_beat - 20)  # Reduce volume of the binaural beat

    return combined
