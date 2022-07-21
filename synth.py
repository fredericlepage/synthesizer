import numpy as np
import pyaudio
import mido
import itertools
import random

DEVICE = ""   # Midi keyboard name

SAMPLE_RATE = 44100
BUFFER_SIZE = 1024
VOICES = 100
DETUNE = 0.2

notes_dict = {}
lfo_dict = {}


p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paFloat32,
                channels=1,
                rate=SAMPLE_RATE,
                output=True,
                frames_per_buffer=BUFFER_SIZE)

def midi_to_freq(midi_note):
    A = 440
    if DETUNE:
        det = random.uniform(-DETUNE,DETUNE)
        return (A / 32) * (2 ** ((midi_note + det - 9) / 12))
    return (A / 32) * (2 ** ((midi_note - 9) / 12))

def gen_sine(freq, amp=1):
    increment = 2*np.pi*freq/SAMPLE_RATE
    return (np.sin(i)*amp for i in itertools.count(start=0, step=increment))

def get_samples():
    return [sum([next(osc) * np.float32(32767) \
            for _, osc in notes_dict.items()]) \
            for _ in range(BUFFER_SIZE)]

# Run the synth
in_port = mido.open_input(DEVICE)
while True:
    if notes_dict:
        sum_samples = get_samples()
        stream.write(np.float32(sum_samples).tobytes())

    msg = in_port.receive(block=False)
    if msg is not None:
        if msg.type == "note_on":
            if len(notes_dict)+1 > VOICES:
                notes_dict.pop(next(iter(notes_dict)))

            note = msg.note
            freq = midi_to_freq(note)
            amp = msg.velocity/127
            notes_dict[note] = gen_sine(freq, amp)

        if msg.type == "note_off" and msg.note in notes_dict.keys():
            del notes_dict[msg.note]




p.terminate()
