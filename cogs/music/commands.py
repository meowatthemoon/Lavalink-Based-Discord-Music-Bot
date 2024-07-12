from dataclasses import dataclass
from enum import Enum, auto


class Command(Enum):
    SEARCH = auto()
    PLAY_PLAYLIST = auto()
    CREATE_PLAYLIST = auto()
    DELETE_PLAYLIST = auto()
    RENAME_PLAYLIST = auto()
    ADD_SONG_PLAYLIST = auto()
    REMOVE_SONG_PLAYLIST = auto()
    QUEUE = auto()
    HISTORY = auto()

@dataclass
class CommandInfo:
    command : Command
    description : str

commands = [
    CommandInfo(command = Command.SEARCH, description = "Search for a Song."),
    CommandInfo(command = Command.PLAY_PLAYLIST, description = "Play Playlist."),
    CommandInfo(command = Command.CREATE_PLAYLIST, description = "Create a Playlist."),
    CommandInfo(command = Command.DELETE_PLAYLIST, description = "Delete a Playlist."),
    CommandInfo(command = Command.RENAME_PLAYLIST, description = "Rename Playlist."),
    # Not yet implemented
    #CommandInfo(command = Command.ADD_SONG_PLAYLIST, description = "Add Song to Playlist."),
    #CommandInfo(command = Command.REMOVE_SONG_PLAYLIST, description = "Remove Song from Playlist."),
    #CommandInfo(command = Command.QUEUE, description = "Show Queue."),
    #CommandInfo(command = Command.HISTORY, description = "Show History.")
]
