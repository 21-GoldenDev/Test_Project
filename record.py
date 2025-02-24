import pyaudio
import wave

# Parameters for recording
FORMAT = pyaudio.paInt16  # Audio format (16-bit PCM)
CHANNELS = 1               # Number of channels (1 for mono)
RATE = 16000               # Sample rate (44.1 kHz)
CHUNK = 1600               # Buffer size
RECORD_SECONDS = 20        # Duration of recording in seconds
WAVE_OUTPUT_FILENAME = "record1.wav"  # Output file name

print("Recording parameters:", FORMAT, CHANNELS, RATE, CHUNK, RECORD_SECONDS)
# Create an interface to PortAudio
audio = pyaudio.PyAudio()
chosen_device_index = -1
for x in range(0,audio.get_device_count()):
    info = audio.get_device_info_by_index(x)
    print(info)
    if info["name"] == "pulse":
        chosen_device_index = info["index"]
        print("Chosen index: ", chosen_device_index)
# Start recording
stream = audio.open(format=FORMAT, channels=CHANNELS,
                    rate=RATE, input_device_index=chosen_device_index, input=True,
                    frames_per_buffer=CHUNK)

print(type(stream))

print("Recording...")

frames = []

for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    frames.append(data)
    # print(data)

print("Finished recording.")

# Stop and close the stream
stream.stop_stream()
stream.close()
audio.terminate()

# Save the recorded data as a WAV file
with wave.open(WAVE_OUTPUT_FILENAME, 'wb') as wf:
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))


