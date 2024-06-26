from typing import List, Dict, Iterator, Tuple

import mido
from mido import MidiFile
from music21 import note as musicnote
from music21 import stream, analysis, pitch


from tabs import Tabs
from exceptions import TrackError


class MIDIParser:
    """
    MIDI file parser

    :param file_path: MIDI file path
    :param track: Track number in the MIDI file to be picked

    Example:

    >>> from tayuya import MIDIParser
    >>> mid = MIDIParser('sample.mid', track=0)
    >>> mid.render_tabs()

    Don't forget to set the `track` argument with the appropriate track
    number desired.
    """

    def __init__(self, file_path: str, track=0):
        self.midi_file = MidiFile(file_path)
        self.track = track
        self.midi_data = self.midi_file.tracks[track]

        # Get time signature
        ts_meta = list(filter(lambda x: x.type == TIME_SIGNATURE,
                              self.midi_data))
        if ts_meta:
            numerator = ts_meta[0].numerator
            denominator = ts_meta[0].denominator
        else:
            numerator = denominator = 4
        self.time_signature = (numerator, denominator)

        self.stream = stream.Stream()

        if not self.midi_data:
            raise TrackError

    def notes_played(self) -> List[Dict]:
        """
        Get all notes played in this MIDI track

        :returns: List of all notes player with note time
        """
        return [
            dict(note=self._midi_to_note(note.note), time=note.time)
            for note in self._on_note()
        ]

    def get_tracks(self) -> Dict:
        """
        Get all tracks of the MIDI file

        :returns: track number and name mapping
        """
        return {idx: track.name for idx, track in enumerate(self.midi_file.tracks)}

    def get_key(self) -> pitch.Pitch:
        """
        Get key of this MIDI track

        refer: http://web.mit.edu/music21/doc/moduleReference/moduleAnalysisDiscrete.html

        We have used Krumhansl-Schmuckler algorithm for key determitination with
        following weightings implementation:

        * Aarden-Essen
        * Bellman-Budge
        * Krumhansl-Schmuckler
        * Krumhansl-Kessler
        * Temperley-Kostka-Payne

        Key which is determined the most by these methods is chosen

        :returns: predicted key of a MIDI track
        """
        note_length: float = 0.0

        for note in self.midi_data:
            if note.type not in [NOTE_ON, NOTE_OFF] or note.is_meta:
                continue
            note_length += note.time
            if note.type == NOTE_ON:
                self.stream.append(musicnote.Note(note.note,
                                   type=self._get_note_type(note_length)))
                note_length = 0.0

        key_weight = analysis.discrete.KeyWeightKeyAnalysis().process(self.stream)
        krumhansl_shmuckler = analysis.discrete.KrumhanslSchmuckler().process(self.stream)
        bellman_budge = analysis.discrete.BellmanBudge().process(self.stream)
        aarden_essen = analysis.discrete.AardenEssen().process(self.stream)
        krumhansl_kessler = analysis.discrete.KrumhanslKessler().process(self.stream)
        temperley_kostka_payne = analysis.discrete.TemperleyKostkaPayne().process(self.stream)

        prediction = list(map(lambda x: (x[0][0], x[0][1]),
                              [key_weight, krumhansl_shmuckler, bellman_budge,
                               aarden_essen, krumhansl_kessler,
                               temperley_kostka_payne]))

        return max(prediction, key=prediction.count)

    def render_tabs(self, **kwargs) -> None:
        """
        Visualize notes in tabulature format
        """
        tabs = Tabs(notes=self.notes_played(), key=self.get_key())
        to_play = tabs.generate_notes()

        return tabs.render(to_play, **kwargs)

    def _on_note(self) -> Iterator:
        """
        Filter all notes which are `on`

        :returns: List of notes which were on
        """
        return filter(
            lambda x: x.type == NOTE_ON, self.midi_data)

    def _midi_to_note(self, midi_note: int) -> str:
        """
        Convert MIDI note to music note

        :param midi_note: MIDI code for this note

        :returns: String notation of MIDI note
        """
        return MIDI_TO_NOTES[midi_note][0]

    def _get_note_type(self, note_length: int) -> str:
        """
        Get note type: `quarter`, `half`, `whole`, `eighth` or `sixteenth`

        :params note_length: length of this note played

        :returns: Type of note played
        """
        num_beats = note_length / self.midi_file.ticks_per_beat

        # Get which note type gets the beat
        beat_note = NUM_TO_NOTES[self.time_signature[1]]

        if num_beats <= 1.5:
            return beat_note
        elif 1.5 < num_beats <= 2.5:
            return NUM_TO_NOTES[self.time_signature[1] // 2]
        else:
            return WHOLE_NOTE
    
    def generate_notes_to_file(self, filename: str):
    # generate_notes fonksiyonu çağrılarak notalar alınıyor
        notes = self.render_tabs()
    # Belirtilen dosyayı yazma modunda açın
        with open(filename, 'w') as file:
        # Her bir notayı dosyaya yazın
         for note in notes:
             file.write(f"{note}\n")
    
        print(f"Notes written to {filename} successfully.")


# Standard tuning of each string
GUITAR_STAFF: dict = {0: 'E', 1: 'A', 2: 'D', 3: 'G', 4: 'B', 5: 'E'}
UKULELE_STAFF: dict = {0: 'G', 1: 'C', 2: 'E', 3: 'A'}

# Number of strings
GUITAR_STRING = 6
UKULELE_STRING = 4

# MIDI metadata
TIME_SIGNATURE = 'time_signature'
NOTE_ON = 'note_on'
NOTE_OFF = 'note_off'
HALF_NOTE = 'half'
WHOLE_NOTE = 'whole'
QUARTER_NOTE = 'quarter'
EIGHTH_NOTE = 'eighth'
SIXTEENTH_NOTE = 'sixteenth'

# Note type to note name mappings
NUM_TO_NOTES = {1: WHOLE_NOTE, 2: HALF_NOTE, 4: QUARTER_NOTE,
                8: EIGHTH_NOTE, 16: SIXTEENTH_NOTE}

# Notes on all strings and fret of a guitar
# This is unused. Can remove
FRET_NOTES = \
    [['F4', 'F#4', 'G4', 'Ab4', 'A4', 'Bb4', 'B4', 'C5', 'C#5', 'D5', 'Eb5', 'E5', 'F5', 'F#5', 'G5', 'Ab5', 'A5', 'Bb5', 'B5', 'C6', 'C#6', 'D6'],  # E
     ['C4', 'C#4', 'D4', 'Eb4', 'E4', 'F4', 'F#4', 'G4', 'Ab4', 'A4', 'Bb4', 'B4', 'C5', 'C#5', 'D5', 'Eb5', 'E5', 'F5', 'F#5', 'G5', 'Ab5', 'A5'],  # B
     ['Ab3', 'A3', 'Bb3', 'B3', 'C4', 'C#4', 'D4', 'Eb4', 'E4', 'F4', 'F#4', 'G4', 'Ab4', 'A4', 'Bb4', 'B4', 'C5', 'C#5', 'D5', 'Eb5', 'E5', 'F5'],  # G
     ['Eb3', 'E3', 'F3', 'F#3', 'G3', 'Ab3', 'A3', 'Bb3', 'B3', 'C4', 'C#4', 'D4', 'Eb4', 'E4', 'F4', 'F#4', 'G4', 'Ab4', 'A4', 'Bb4', 'B4', 'C5'],  # D
     ['Bb2', 'B2', 'C3', 'C#3', 'D3', 'Eb3', 'E3', 'F3', 'F#3', 'G3', 'Ab3', 'A3', 'Bb3', 'B3', 'C4', 'C#4', 'D4', 'Eb4', 'E4', 'F4', 'F#4', 'G4'],  # A
     ['F2', 'F#2', 'G2', 'Ab2', 'A2', 'Bb2', 'B2', 'C3', 'C#3', 'D3', 'Eb3', 'E3', 'F3', 'F#3', 'G3', 'Ab3', 'A3', 'Bb3', 'B3', 'C4', 'C#4', 'D4']]  # E
    #                3           5            7            9                  12                 15           17           19          21

TRACK_ERROR_MESSAGE = 'No track with string instrument found'

# MIDI value to notes mapping
MIDI_TO_NOTES = {
    0: [''],
    1: [''],
    10: [''],
    100: ['E7'],
    101: ['F7'],
    102: ['F#7', 'Gb7'],
    103: ['G7'],
    104: ['G#7', 'Ab7'],
    105: ['A7'],
    106: ['A#7', 'Bb7'],
    107: ['B7'],
    108: ['C8'],
    109: ['C#8', 'Db8'],
    11: [''],
    110: ['D8'],
    111: ['D#8', 'Eb8'],
    112: ['E8'],
    113: ['F8'],
    114: ['F#8', 'Gb8'],
    115: ['G8'],
    116: ['G#8', 'Ab8'],
    117: ['A8'],
    118: ['A#8', 'Bb8'],
    119: ['B8'],
    12: [''],
    120: ['C9'],
    121: ['C#9', 'Db9'],
    122: ['D9'],
    123: ['D#9', 'Eb9'],
    124: ['E9'],
    125: ['F9'],
    126: ['F#9', 'Gb9'],
    127: ['G9'],
    13: [''],
    14: [''],
    15: [''],
    16: [''],
    17: [''],
    18: [''],
    19: [''],
    2: [''],
    20: [''],
    21: ['A0'],
    22: ['A#0', 'Bb0'],
    23: ['B0'],
    24: ['C1'],
    25: ['C#1', 'Db1'],
    26: ['D1'],
    27: ['D#1', 'Eb1'],
    28: ['E1'],
    29: ['F1'],
    3: [''],
    30: ['F#1', 'Gb1'],
    31: ['G1'],
    32: ['G#1', 'Ab1'],
    33: ['A1'],
    34: ['A#1', 'Bb1'],
    35: ['B1'],
    36: ['C2'],
    37: ['C#2', 'Db2'],
    38: ['D2'],
    39: ['D#2', 'Eb2'],
    4: [''],
    40: ['E2'],
    41: ['F2'],
    42: ['F#2', 'Gb2'],
    43: ['G2'],
    44: ['G#2', 'Ab2'],
    45: ['A2'],
    46: ['A#2', 'Bb2'],
    47: ['B2'],
    48: ['C3'],
    49: ['C#3', 'Db3'],
    5: [''],
    50: ['D3'],
    51: ['D#3', 'Eb3'],
    52: ['E3'],
    53: ['F3'],
    54: ['F#3', 'Gb3'],
    55: ['G3'],
    56: ['G#3', 'Ab3'],
    57: ['A3'],
    58: ['A#3', 'Bb3'],
    59: ['B3'],
    6: [''],
    60: ['C4'],
    61: ['C#4', 'Db4'],
    62: ['D4'],
    63: ['D#4', 'Eb4'],
    64: ['E4'],
    65: ['F4'],
    66: ['F#4', 'Gb4'],
    67: ['G4'],
    68: ['G#4', 'Ab4'],
    69: ['A4'],
    7: [''],
    70: ['A#4', 'Bb4'],
    71: ['B4'],
    72: ['C5'],
    73: ['C#5', 'Db5'],
    74: ['D5'],
    75: ['D#5', 'Eb5'],
    76: ['E5'],
    77: ['F5'],
    78: ['F#5', 'Gb5'],
    79: ['G5'],
    8: [''],
    80: ['G#5', 'Ab5'],
    81: ['A5'],
    82: ['A#5', 'Bb5'],
    83: ['B5'],
    84: ['C6'],
    85: ['C#6', 'Db6'],
    86: ['D6'],
    87: ['D#6', 'Eb6'],
    88: ['E6'],
    89: ['F6'],
    9: [''],
    90: ['F#6', 'Gb6'],
    91: ['G6'],
    92: ['G#6', 'Ab6'],
    93: ['A6'],
    94: ['A#6', 'Bb6'],
    95: ['B6'],
    96: ['C7'],
    97: ['C#7', 'Db7'],
    98: ['D7'],
    99: ['D#7', 'Eb7']
}

# Note to string and fret mappings
NOTE_TO_STRING =  \
    {'F4': {1: 1, 2: 6, 3: 10, 4: 15, 5: 20, 6: ''},
     'F#4': {1: 2, 2: 7, 3: 11, 4: 16, 5: 21, 6: ''},
     'G4': {1: 3, 2: 8, 3: 12, 4: 17, 5: 22, 6: ''},
     'Ab4': {1: 4, 2: 9, 3: 13, 4: 18, 5: '', 6: ''},
     'G#4': {1: 4, 2: 9, 3: 13, 4: 18, 5: '', 6: ''},
     'A4': {1: 5, 2: 10, 3: 14, 4: 19, 5: '', 6: ''},
     'Bb4': {1: 6, 2: 11, 3: 15, 4: 20, 5: '', 6: ''},
     'A#4': {1: 6, 2: 11, 3: 15, 4: 20, 5: '', 6: ''},
     'B4': {1: 7, 2: 12, 3: 16, 4: 21, 5: '', 6: ''},
     'C5': {1: 8, 2: 13, 3: 17, 4: 22, 5: '', 6: ''},
     'C#5': {1: 9, 2: 14, 3: 18, 4: '', 5: '', 6: ''},
     'D5': {1: 10, 2: 15, 3: 19, 4: '', 5: '', 6: ''},
     'Eb5': {1: 11, 2: 16, 3: 20, 4: '', 5: '', 6: ''},
     'D#5': {1: 11, 2: 16, 3: 20, 4: '', 5: '', 6: ''},
     'E5': {1: 12, 2: 17, 3: 21, 4: '', 5: '', 6: ''},
     'F5': {1: 13, 2: 18, 3: 22, 4: '', 5: '', 6: ''},
     'F#5': {1: 14, 2: 19, 3: '', 4: '', 5: '', 6: ''},
     'G5': {1: 15, 2: 20, 3: '', 4: '', 5: '', 6: ''},
     'Ab5': {1: 16, 2: 21, 3: '', 4: '', 5: '', 6: ''},
     'G#5': {1: 16, 2: 21, 3: '', 4: '', 5: '', 6: ''},
     'A5': {1: 17, 2: 22, 3: '', 4: '', 5: '', 6: ''},
     'Bb5': {1: 18, 2: '', 3: '', 4: '', 5: '', 6: ''},
     'A#5': {1: 18, 2: '', 3: '', 4: '', 5: '', 6: ''},
     'B5': {1: 19, 2: '', 3: '', 4: '', 5: '', 6: ''},
     'C6': {1: 20, 2: '', 3: '', 4: '', 5: '', 6: ''},
     'C#6': {1: 21, 2: '', 3: '', 4: '', 5: '', 6: ''},
     'D6': {1: 22, 2: '', 3: '', 4: '', 5: '', 6: ''},
     'C4': {1: '', 2: 1, 3: 5, 4: 10, 5: 15, 6: 20},
     'C#4': {1: '', 2: 2, 3: 6, 4: 11, 5: 16, 6: 21},
     'D4': {1: '', 2: 3, 3: 7, 4: 12, 5: 17, 6: 22},
     'Eb4': {1: '', 2: 4, 3: 8, 4: 13, 5: 18, 6: ''},
     'D#4': {1: '', 2: 4, 3: 8, 4: 13, 5: 18, 6: ''},
     'E4': {1: '', 2: 5, 3: 9, 4: 14, 5: 19, 6: ''},
     'Ab3': {1: '', 2: '', 3: 1, 4: 6, 5: 11, 6: 16},
     'G#3': {1: '', 2: '', 3: 1, 4: 6, 5: 11, 6: 16},
     'A3': {1: '', 2: '', 3: 2, 4: 7, 5: 12, 6: 17},
     'Bb3': {1: '', 2: '', 3: 3, 4: 8, 5: 13, 6: 18},
     'A#3': {1: '', 2: '', 3: 3, 4: 8, 5: 13, 6: 18},
     'B3': {1: '', 2: '', 3: 4, 4: 9, 5: 14, 6: 19},
     'Eb3': {1: '', 2: '', 3: '', 4: 1, 5: 6, 6: 11},
     'D#3': {1: '', 2: '', 3: '', 4: 1, 5: 6, 6: 11},
     'E3': {1: '', 2: '', 3: '', 4: 2, 5: 7, 6: 12},
     'F3': {1: '', 2: '', 3: '', 4: 3, 5: 8, 6: 13},
     'F#3': {1: '', 2: '', 3: '', 4: 4, 5: 9, 6: 14},
     'G3': {1: '', 2: '', 3: '', 4: 5, 5: 10, 6: 15},
     'Bb2': {1: '', 2: '', 3: '', 4: '', 5: 1, 6: 6},
     'A#2': {1: '', 2: '', 3: '', 4: '', 5: 1, 6: 6},
     'B2': {1: '', 2: '', 3: '', 4: '', 5: 2, 6: 7},
     'C3': {1: '', 2: '', 3: '', 4: '', 5: 3, 6: 8},
     'C#3': {1: '', 2: '', 3: '', 4: '', 5: 4, 6: 9},
     'D3': {1: '', 2: '', 3: '', 4: '', 5: 5, 6: 10},
     'F2': {1: '', 2: '', 3: '', 4: '', 5: '', 6: 1},
     'F#2': {1: '', 2: '', 3: '', 4: '', 5: '', 6: 2},
     'G2': {1: '', 2: '', 3: '', 4: '', 5: '', 6: 3},
     'Ab2': {1: '', 2: '', 3: '', 4: '', 5: '', 6: 4},
     'G#2': {1: '', 2: '', 3: '', 4: '', 5: '', 6: 4},
     'A2': {1: '', 2: '', 3: '', 4: '', 5: '', 6: 5},
     'B1': {1: '', 2: '', 3: '', 4: '', 5: '', 6: 5}}

# Max length of tablature in CLI mode
MAX_RENDER_COLUMNS = 70

TAB_LINE_CHAR = '-'

FILLER_TEXT = """
********************************
*           NEXT TAB           *
********************************
"""

# Common scale an steps mappings
SCALE = {
    'major': [2, 2, 1, 2, 2, 2, 1],
    'ionian': [2, 2, 1, 2, 2, 2, 1],
    'dorian': [2, 1, 2, 2, 2, 1, 2],
    'phrygian': [1, 2, 2, 2, 1, 2, 2],
    'lydian': [2, 2, 2, 1, 2, 2, 1],
    'mixolydian': [2, 2, 1, 2, 2, 1, 2],
    'locrian': [1, 2, 2, 1, 2, 2, 2],
    'minor': [2, 1, 2, 2, 1, 2, 2],
    'aeolian': [2, 1, 2, 2, 1, 2, 2],
    'jazz_minor': [2, 1, 2, 2, 2, 2, 1],
}


MAJOR = 'major'
IONIAN = 'ionian'
DORIAN = 'dorian'
PHRYGIAN = 'phrygian'
LYDIAN = 'lydian'
LOCRIAN = 'locrian'
MINOR = 'minor'
AEOLIAN = 'aeolian'
JAZZ_MINOR = 'jazz_minor'
