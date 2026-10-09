import subprocess

text = "Please choose a plate."

def speak(text):
    subprocess.run(["say", text], check=False)

speak(text)
