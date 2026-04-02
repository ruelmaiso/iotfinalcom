import sys
import time
import os

# Clear terminal (Windows / Linux / Mac)
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

# Hide cursor
def hide_cursor():
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()

# Show cursor again (important after program ends)
def show_cursor():
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()

# Typewriter effect (character by character)
def type_line(text, char_delay=0.05):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(char_delay)
    print()  

def print_lyrics():
    lyrics = [
        ("Chasing down this cure, no plan in hand", 0.06),
        ("just your pulse, my racing guide in the dark", 0.09),
        ("just knowing with conviction from the start", 0.07),
        
        ("The moment your eyes made an introduction", 0.09),
        ("I found my second violent breath of life", 0.07),
        ("Flawless to the point of being godly", 0.07),
       
        ("Yeah, i fell hard for your imperfections", 0.08),
        ("And now its like the weather is slightly warmer", 0.08),
 
    ]

  
    line_delay = 0.5  

    for line, speed in lyrics:
        type_line(line, speed)
        time.sleep(line_delay)

try:
    clear()
    hide_cursor()
    print_lyrics()
finally:
    show_cursor()