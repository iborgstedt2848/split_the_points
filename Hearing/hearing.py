import vosk
import pyaudio
import json


# Here I have downloaded this model to my PC, extracted the files
# and saved it in local directory
# Set the model path
model_path = "./Hearing/vosk-model-en-us-0.42-gigaspeech"
# Initialize the model with model-path
model = vosk.Model(model_path)


# if you don't want to download the model, just mention "lang" argument
# in vosk.Model() and it will download the right  model, here the language is
# US-English
# model = vosk.Model(lang="en-us")

# Create a recognizer
rec = vosk.KaldiRecognizer(model, 16000)


# Open the microphone stream
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer= 4096)

def listen():
    while True:
        data = stream.read(4096, exception_on_overflow=False)  # read in chunks of this many bytes
        
        if rec.AcceptWaveform(data):  # accept waveform of input voice
            # Parse the JSON result and get the recognized text
            result = json.loads(rec.Result())
            recognized_text = result.get('text', '')

            if recognized_text:  # Check if recognized_text is not empty
                return recognized_text