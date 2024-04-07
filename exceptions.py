


class TrackError(Exception):
    """
    Custom error for failure in handling of MIDI track
    """
    def __init__(self):
        self.msg = "TRACK_ERROR_MESSAGE"

    def __str__(self):
        return repr(self.msg)

