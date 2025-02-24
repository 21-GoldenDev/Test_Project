import io
import grpc

import riva.client

# Instantiate client
auth = riva.client.Auth(uri='localhost:50051')
riva_asr = riva.client.ASRService(auth)

# path = "tutorials/audio_samples/interview-with-bill.wav"
# path = "tutorials/audio_samples/en-US_sample.wav"
path = "./test_audio/test.wav"
with io.open(path, 'rb') as fh:
    content = fh.read()

# Creating RecognitionConfig
config = riva.client.RecognitionConfig(
  language_code="en-US",
  max_alternatives=1,
  enable_automatic_punctuation=True,
  enable_word_time_offsets=True,
)

riva.client.asr.add_speaker_diarization_to_config(config, diarization_enable=True, diarization_max_speakers=8)

# ASR inference call with Recognize
response = riva_asr.offline_recognize(content, config)
print("ASR Transcript with Speaker Diarization:\n", response)

# Pretty print transcript with color coded speaker tags. Black color text indicates no speaker tag was assigned.
for result in response.results:
    for word in result.alternatives[0].words:
        color = '\033['+ str(30 + word.speaker_tag) + 'm'
        print(color, word.word, end="")
      

