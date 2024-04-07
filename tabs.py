from typing import Dict, Tuple, List

from music21 import scale

class Tabs:
    """
    Tab generator
    """

    def __init__(self, notes: List[Dict], key: Tuple):
        self.notes = notes
        self.key = key
        self.notes_cache: Dict = {}

    def generate_notes(self) -> List[Tuple[str, int, int]]:
        """
        Get list of all notes to play with their fret and string positions

        :param start_from: (fret, string, scale_notes), start position of the tab

        :returns: (note, string, fret) list of notes to play
        """
        fret, _, scale_notes = self.find_start()
        to_play: List = []

        for note in self.notes:
            note_info = NOTE_TO_STRING.get(note['note'])  # NOTE_TO_STRING sözlüğünden ilgili nota bilgilerini alın
            if note_info is None:  # Eğer bu nota bilgileri yoksa, geç
                continue
            note_fret, note_string = self.note_nearest_to_fret(fret, note['note'], scale_notes)
            to_play.append((note['note'], note_string, note_fret))
            fret = note_fret

        return to_play

    def note_nearest_to_fret(self, fret: int, note: str, scale_notes: List[Tuple]) -> Tuple[int, int]:
        note_info = NOTE_TO_STRING.get(note)
            
        min_fret = min_string = min_diff = 999
        if note_info:
        
         for note_string, note_fret in note_info.items():
            
            if not note_fret:
                continue

            if (note_fret, note_string) in scale_notes:
                return (note_fret, note_string)

            if self.notes_cache.get(note):
                return self.notes_cache[note]
           
            diff = abs(note_fret - fret)
            if diff <= min_diff:
                min_diff = diff
                min_fret = note_fret
                min_string = note_string

         self.notes_cache[note] = (min_fret, min_string)
         return (min_fret, min_string)
        return (None, None)

    def find_start(self) -> Tuple[int, int, List[Tuple]]:
        max_count: int = 0
        start_fret = start_string = 0
        start_scale_notes: List = []

        pitch, scale_type = self.key
        pitch = self._fix_note_name(pitch)
        this_scale_step = SCALE[scale_type]

        sc = self._get_scale()

        this_scale_notes = [note.nameWithOctave for note in sc.pitches]
        first_note = this_scale_notes[0]

        note_info = NOTE_TO_STRING[self._fix_note_name(first_note)]

        for note_string, note_fret in note_info.items():
            string: int = note_string
            fret: int = note_fret
            num_notes: int = 0
            step: int = 0
            span: int = 8
            note_list: List = [(fret, string)]

            while string > 0 and span > 0 and note_fret:
                fret += this_scale_step[step]
                step += 1
                num_notes += 1
                note_list.append((fret, string))

                if step >= len(SCALE[scale_type]):
                    step = 0
                if fret > note_fret + 3:
                    fret -= 4 if string == 2 else 5
                    string -= 1
                if num_notes > max_count:
                    max_count = num_notes
                    start_fret = note_fret
                    start_string = note_string
                    start_scale_notes = note_list

                span -= 1

        return start_fret, start_string, start_scale_notes
 
    def render(self, notes_list: List[Dict], **kwargs) -> List[str]:
     staff_length = kwargs.get('staff_length', MAX_RENDER_COLUMNS)
     fretboard = ['' for _ in range(GUITAR_STRING)]
     output = []

     for note, note_string, note_fret in notes_list:
         idx_note_string = int(note_string) - 1

         for idx, fretboard_string in enumerate(fretboard):
            if len(fretboard_string) > len(fretboard[idx_note_string]):
                diff = len(fretboard_string) - len(fretboard[idx_note_string])
                fretboard[idx_note_string] += f'{TAB_LINE_CHAR}' * diff

         fret = str(note_fret)
         fretboard[idx_note_string] += f'{TAB_LINE_CHAR}{fret}{TAB_LINE_CHAR}'

     max_staff_length = len(max(fretboard, key=len))

     for idx, string in enumerate(fretboard):
         diff = max_staff_length - len(string)
         fretboard[idx] = fretboard[idx] + TAB_LINE_CHAR * diff

     break_point = staff_length

     for string in fretboard:
         if string[break_point] != TAB_LINE_CHAR:
             break_point += 1
             continue

     string_idx = 0
     start = 0
     end = break_point
     while True:
         if not fretboard[string_idx][start:] and start > staff_length:
             break
         for idx, string in enumerate(fretboard):
             output.append(GUITAR_STAFF[idx] + string[start:end])

         string_idx += 1
         string_idx = string_idx % GUITAR_STRING
         start = end
         end = start + break_point

         output.append('')

     return output

    def _fix_note_name(self, pitch) -> str:
        if isinstance(pitch, str):
            name = pitch
        else:
            name = pitch.nameWithOctave
        name = name.replace('-', 'b')
        try:
            int(name[-1])
        except ValueError:
            name += str(pitch.implicitOctave)
        return name

    def _get_scale(self):
        pitch, scale_type = self.key

        if scale_type in [MAJOR, IONIAN]:
            return scale.MajorScale(pitch)
        elif scale_type in [MINOR, AEOLIAN]:
            return scale.MinorScale(pitch)
        elif scale_type == DORIAN:
            return scale.DorianScale(pitch)
        elif scale_type == PHRYGIAN:
            return scale.PhrygianScale(pitch)
        elif scale_type == LYDIAN:
            return scale.LydianScale(pitch)
        elif scale_type == LOCRIAN:
            return scale.LocrianScale(pitch)
        else:
            return scale.MajorScale(pitch)



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
NOTE_TO_STRING =  {
    'F4': {1: 1, 2: 6, 3: 10, 4: 15, 5: 20, 6: ''},
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
    'B1': {1: '', 2: '', 3: '', 4: '', 5: '', 6: 5},
    'C#2': {1: '', 2: '', 3: '', 4: '', 5: '', 6: ''},
    'Db2': {1: '', 2: '', 3: '', 4: '', 5: '', 6: ''},
    'D2': {1: '', 2: '', 3: '', 4: '', 5: '', 6: ''},
    'D#2': {1: '', 2: '', 3: '', 4: '', 5: '', 6: ''},
    'Eb2': {1: '', 2: '', 3: '', 4: '', 5: '', 6: ''},
    'E2': {1: '', 2: '', 3: '', 4: '', 5: '', 6: ''},
    'F2': {1: '', 2: '', 3: '', 4: '', 5: '', 6: ''},
    'F#1': {1: '', 2: '', 3: '', 4: '', 5: '', 6: ''},
    'Gb1': {1: '', 2: '', 3: '', 4: '', 5: '', 6: ''},
    'G1': {1: '', 2: '', 3: '', 4: '', 5: '', 6: ''},
    'G#1': {1: '', 2: '', 3: '', 4: '', 5: '', 6: ''},
    'Ab1': {1: '', 2: '', 3: '', 4: '', 5: '', 6: ''},
    'A1': {1: '', 2: '', 3: '', 4: '', 5: '', 6: ''},
    'A#1': {1: '', 2: '', 3: '', 4: '', 5: '', 6: ''},
    'Bb1': {1: '', 2: '', 3: '', 4: '', 5: '', 6: ''},
    'B1': {1: '', 2: '', 3: '', 4: '', 5: '', 6: ''},
    'F7': {1: 14, 2: 19, 3: '', 4: '', 5: '', 6: ''}
}

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
