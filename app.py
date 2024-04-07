from midi import MIDIParser 

parser = MIDIParser("C:/Users/emre-/OneDrive/Masaüstü/Yeni klasör/a.mid")  # MIDI dosyasının adını düzeltin
parser.generate_notes_to_file("notes.txt")