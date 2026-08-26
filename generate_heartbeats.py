import numpy as np
from scipy.io import wavfile
import os

# Parameters
SAMPLE_RATE = 44100
DURATION = 30 # seconds

def generate_lub_dub(t, start_time):
    # Lub (S1) is lower frequency, longer duration
    # Dub (S2) is slightly higher frequency, shorter duration
    
    # S1 params
    f1 = 70.0 # Hz
    duration1 = 0.12 # s
    
    # S2 params
    f2 = 100.0 # Hz
    duration2 = 0.08 # s
    
    # Time offset for S2
    systole_duration = 0.30 # s (time between S1 and S2)
    
    # Generate S1
    env1 = np.exp(-15 * (t - start_time)) * (t >= start_time) * (t < start_time + duration1)
    s1 = env1 * np.sin(2 * np.pi * f1 * t)
    
    # Generate S2
    start2 = start_time + systole_duration
    env2 = np.exp(-20 * (t - start2)) * (t >= start2) * (t < start2 + duration2)
    s2 = env2 * np.sin(2 * np.pi * f2 * t)
    
    return s1 + s2

def generate_rhythm(bpm, duration, filename, is_arrhythmia=False):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    audio = np.zeros_like(t)
    
    beat_interval = 60.0 / bpm
    current_time = 0.5 # start delay
    
    while current_time < duration - 1.0:
        audio += generate_lub_dub(t, current_time)
        
        if is_arrhythmia:
            # Randomize interval
            current_interval = beat_interval * np.random.uniform(0.6, 1.4)
        else:
            current_interval = beat_interval
            
        current_time += current_interval
        
    # Normalize
    audio = audio / np.max(np.abs(audio))
    
    # Convert to 16-bit PCM
    audio_int16 = np.int16(audio * 32767)
    
    output_path = os.path.join(r"c:\Users\user\Music\Med loyiha yurak ritmi", filename)
    wavfile.write(output_path, SAMPLE_RATE, audio_int16)
    print(f"Generated {filename}")

if __name__ == "__main__":
    # Create directory if it doesn't exist
    os.makedirs(r"c:\Users\user\Music\Med loyiha yurak ritmi", exist_ok=True)
    
    generate_rhythm(72, DURATION, "normal_72bpm.wav")
    generate_rhythm(130, DURATION, "taxikardiya_130bpm.wav")
    generate_rhythm(45, DURATION, "bradikardiya_45bpm.wav")
    generate_rhythm(75, DURATION, "aritmiya_75bpm.wav", is_arrhythmia=True)
    print("Barcha fayllar muvaffaqiyatli yaratildi.")
