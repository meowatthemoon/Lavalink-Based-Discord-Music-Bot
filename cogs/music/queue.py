from random import randint
from wavelink.tracks import Playable

class Queue:
    def __init__(self):
        self._tracks : list[Playable] = []
        self._index : int = -1

    def add_track(self, track : Playable) -> bool:
        if track is None:
            return False
        
        self._tracks.append(track)
        return True
    
    def get_current_track(self) -> Playable:
        if self._index < 0:
            return None
        return self._tracks[self._index]
    
    def get_queued_tracks(self) -> list[Playable]:
        if self._index == -1:
            return self._tracks
        
        return self._tracks[self._index + 1:]
    
    def get_history_tracks(self) -> list[Playable]:
        return self._tracks[:self._index]
    
    def get_next_track(self) -> Playable:
        self._index += 1
        return self.get_current_track()
    
    def get_queue_length(self) -> int:
        return len(self.get_queued_tracks())
    
    def is_empty(self) -> bool:
        return not self.get_queue_length() > 0
    
    def next(self) -> Playable:
        if self.get_queue_length == 0:
            return None
        self._index += 1
        return self._tracks[self._index]
    
    def previous(self) -> Playable:
        if self.get_queue_length == 0:
            return None
        self._index -= 1
        return self._tracks[self._index]
    
    def remove_track(self, index : int) -> bool:
        if index < len(self._tracks):
            del self._tracks[index]
            return True

        return False
    
    def reset(self):
        self._tracks = []
        self._index = -1


    def skip_by(self, jump : int):
        self._index += jump
    
    def shuffle(self):
        shuffled_tracks = []

        queued_tracks = self.get_queued_tracks()
        while len(queued_tracks) > 0:
            index = randint(0, len(queued_tracks) - 1)
            shuffled_tracks.append(queued_tracks[index])
            del queued_tracks[index]
        self._tracks = self.get_history_tracks() + [self.get_current_track()] + shuffled_tracks
