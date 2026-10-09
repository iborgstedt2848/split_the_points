from Hearing.hearing import listen
from Speaking.speaking import speak


def main():
    # Call the listen function from Hearing module
    text = listen()
    # Call the say function from Speaking module
    speak(text)


if __name__ == '__main__':
    print("Listening to repeat after you")
    while True:
        main()
