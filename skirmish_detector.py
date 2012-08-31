#!/usr/bin/env python2.5 # Python2.5 because that's what PyAudio binaries for osx target...
'''Detects bouts of loudness that are indicative of a nerf skirmish.
When it gets sufficiently loud, it announces it, and then cools off when it gets
quiet again. Eventually it goes back into peace, which it also announces.
If someone fires while it's cooling down, it resets and returns to skirmish mode.'''
import numpy
import analyse
import pyaudio
import socket

SECONDS_OF_PEACE = 30
MAXIMUM_LOUDNESS = 10
SECONDS_OF_WAR = 5

def message(string):
    '''Send a message to a twisted server listening on port 4321.
    It expects multiple messages to be separated with "\n".
    '''
    print string
    HOST, PORT = 'localhost', 4321
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((HOST, PORT))
        sock.send(string)
    except socket.error, exc:
        print "ERROR:", exc
    sock.close()

def detect():
    p = pyaudio.PyAudio()

    # Open input stream, 16-bit mono at 44100 Hz
    # On my system, device 2 is a USB microphone, your number may differ.
    stream = p.open(
        format = pyaudio.paInt16,
        channels = 1,
        rate = 44100,
        input = True)

    timer = 0
    state = "PEACE"
    doomclock = SECONDS_OF_WAR
    while True:
        # TODO: At certain times of day, skip even listening.

        # Read raw microphone data
        rawsamps = stream.read(1024*50) # 1024*50 is about one second of data.

        # Convert raw data to NumPy array
        samps = numpy.fromstring(rawsamps, dtype=numpy.int16)

        # Get the loudness.
        loudness = abs(analyse.loudness(samps))

        if loudness < MAXIMUM_LOUDNESS:
            print "Loudness over threshold: %.2f" % loudness

        # If it gets loud, and we were previously at peace or almost peace, restart the countdown.
        if loudness < MAXIMUM_LOUDNESS:
            if doomclock > 0:
                # Tick down the time til war
                doomclock -= 1
            else:
                # WAR! Reset the doom clock.
                doomclock = SECONDS_OF_WAR
                if state == "PEACE":
                    message("A skirmish has broken out!")
                elif state == "TENSIONS":
                    message("Someone fanned the flames of war!")
                timer = SECONDS_OF_PEACE
                state = "SKIRMISH"

        # When it's quiet and we were almost at peace or at war, tick down the countdown.
        if loudness > MAXIMUM_LOUDNESS and state in ("TENSIONS", "SKIRMISH"):
            if doomclock < SECONDS_OF_WAR:
                # Cool down the doomclock.
                doomclock += 1
            if state == "TENSIONS":
                timer -= 1
            state = "TENSIONS"

        # If the time has elapsed and we were almost at peace, make peace.
        if timer is 0 and state == "TENSIONS":
            state = "PEACE"
            message("Peace has spread across the land.")

if __name__ == "__main__":
    detect()


