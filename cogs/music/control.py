from dataclasses import dataclass
from datetime import timedelta
from time import time
from typing import Callable

from discord import Message, Reaction, TextChannel, Member

from cogs.music.commands import commands, Command
from cogs.music.database import Database
from cogs.music.logger import Logger
from cogs.music.menus.menu import Menu
from cogs.music.menus.player_menu import PlayerMenu
from config import SELECTION_WAIT_TIME

@dataclass
class Request:
    author_id : int
    state_function : Callable[[Reaction, Message, Member], None]
    state_value : str

class Control:
    def __init__(self, text_channel : TextChannel, database : Database, logger : Logger):
        self.__database : Database = database
        self.__logger : Logger = logger
        self.__initialized : bool = False
        self.__text_channel : TextChannel = text_channel
        self.__comand_menu : Menu = Menu(
            text_channel = text_channel,
            options = [command.description for command in commands],
            fixed = True
        )
        self.__selection_menu : Menu = Menu(
            text_channel = text_channel,
            default_message = "> Select a command above."
        )
        self.__player_menu = PlayerMenu(text_channel = text_channel)

        self.__requests : dict[int, Request] = {}
        self.__active_author_id : int = 0
        self.__active_author_timestamp : int = 0
        self.__start_function  : Callable[[Reaction, Message, Member], None] = self.__command_selection
        self.__searched_tracks : list = None

    async def setup(self):
        await self.__comand_menu.display()
        await self.__selection_menu.display()
        await self.__player_menu.display()

        self.__initialized = True

    def reacted_to_me(self, reaction : Reaction) -> bool:
        if not self.__initialized:
            return False
        
        return self.__comand_menu.reacted_to_me(reaction = reaction) or self.__selection_menu.reacted_to_me(reaction = reaction) or self.__player_menu.reacted_to_me(reaction = reaction)
    
    async def __make_selection_request(self, author_id : int, options : list[str], header : str = "") -> bool:
        if author_id == self.__active_author_id:
            self.__selection_menu.change_options(options = options)
            await self.__selection_menu.display(header = header)
            return True
        
        if time() - self.__active_author_timestamp < SELECTION_WAIT_TIME:
            return False
        
        self.__selection_menu.change_options(options = options)
        await self.__selection_menu.display(header = header)
        
        self.__active_author_id = author_id
        self.__active_author_timestamp = time()
        
        return True
    
    async def __reset_selection(self):
        self.__selection_menu.change_options(options = [])
        await self.__selection_menu.display()
        self.__active_author_id = 0
        self.__active_author_timestamp = 0
        self.__searched_tracks = None

    async def song_ended_notification(self):
        await self.__player_menu.play_next_track()

    
    async def process_input(self, reaction : Reaction = None, message : Message = None, user : Member = None):
        if not self.__initialized:
            if message:
                await message.delete()
            return
        
        assert reaction or message, "[ERROR] Control - Process Input - Did not receive either reaction or message."

        author_id = message.author.id if message else user.id

        if message and message.channel.id != self.__text_channel.id:
            return

        if reaction and self.__player_menu.reacted_to_me(reaction = reaction):
            return await self.__player_reaction(reaction = reaction, user = user)

        if author_id not in self.__requests:
            self.__requests[author_id] = Request(author_id = author_id, state_function = self.__start_function, state_value = "")

        return await self.__requests[author_id].state_function(reaction = reaction, message = message, user = user)
    
    async def __command_selection(self, reaction : Reaction = None, message : Message = None, user : Member = None):
        # Command select must receive a reaction, not a message
        if message:
            return await message.delete()
        
        # Must click on the command menu not on selection
        if not self.__comand_menu.reacted_to_me(reaction = reaction):
            return

        index = await self.__comand_menu.get_selection(reaction = reaction)

        if index == -1:
            return   
        
        command_info = commands[index]
        command = command_info.command

        if command is Command.CREATE_PLAYLIST:
            self.__requests[user.id].state_function = self.__create_playlist
            return await self.__logger.send(text = f"<@{user.id}> What is the name of the playlist?")
        
        if command is Command.DELETE_PLAYLIST:
            playlists = self.__database.get_playlists(author_id = user.id)

            if len(playlists) == 0:
                self.__requests[user.id].state_function = self.__start_function
                return await self.__logger.send(f"<@{user.id}>  You have no playlists.")
            
            playlist_names = [playlist.name for playlist in playlists]

            allowed = await self.__make_selection_request(author_id = user.id, options = playlist_names, header = f"<@{user.id}> Select **Playlist** to delete:")

            if not allowed:
                self.__requests[user.id].state_function = self.__start_function
                return            
            
            self.__requests[user.id].state_function = self.__delete_playlist
            return
        
        if command is Command.RENAME_PLAYLIST:
            playlists = self.__database.get_playlists(author_id = user.id)

            if len(playlists) == 0:
                self.__requests[user.id].state_function = self.__start_function
                return await self.__logger.send(f" <@{user.id}> You have no playlists.")
            
            playlist_names = [playlist.name for playlist in playlists]

            allowed = await self.__make_selection_request(author_id = user.id, options = playlist_names, header = f"<@{user.id}> Select **Playlist** to rename:")

            if not allowed:
                self.__requests[user.id].state_function = self.__start_function
                return            
            
            self.__requests[user.id].state_function = self.__rename_playlist_select
            return
        
        if command is Command.SEARCH:
            allowed = await self.__make_selection_request(author_id = user.id, options = [])
            if not allowed:
                self.__requests[user.id].state_function = self.__start_function
                return
            
            await self.__logger.send(text = f"<@{user.id}>  What song do you want to search for?")
            self.__requests[user.id].state_function = self.__query_search_song
            return

        if command is Command.PLAY_PLAYLIST:
            playlists = self.__database.get_playlists(author_id = user.id)

            if len(playlists) == 0:
                self.__requests[user.id].state_function = self.__start_function
                return await self.__logger.send(f"<@{user.id}>  You have no playlists.")
            
            playlist_names = [playlist.name for playlist in playlists]

            allowed = await self.__make_selection_request(author_id = user.id, options = playlist_names, header = f"<@{user.id}> Select **Playlist** to play:")

            if not allowed:
                self.__requests[user.id].state_function = self.__start_function
                return            
            
            self.__requests[user.id].state_function = self.__play_playlist
            return

        print(f"Implement me at command selection state for command : {command}")

    async def __create_playlist(self, reaction : Reaction = None, message : Message = None, user : Member = None):
        if reaction:
            if self.__comand_menu.reacted_to_me(reaction = reaction):
                self.__requests[user.id].state_function = self.__command_selection
                return await self.__requests[user.id].state_function(reaction = reaction, message = message, user = user)
            return            
        
        playlist_name = message.content
        await message.delete()

        db_response = self.__database.create_playlist(playlist_name = playlist_name, author_id = message.author.id)

        del self.__requests[message.author.id]      
            
        return await self.__logger.send(db_response.message)
    
    async def __delete_playlist(self, reaction : Reaction = None, message : Message = None, user : Member = None):
        if message:
            return await message.delete()
        
        self.__requests[user.id].state_function = self.__start_function

        if user.id != self.__active_author_id:
            return
        
        if self.__comand_menu.reacted_to_me(reaction = reaction):
            return await self.__requests[user.id].state_function(message = message, reaction = reaction, user = user)
        
        option_index = await self.__selection_menu.get_selection(reaction = reaction)
        if option_index == -1:
            return
        
        playlist_name = self.__selection_menu.get_option(index = option_index)

        response = self.__database.delete_playlist(author_id = user.id, playlist_name = playlist_name)
        await self.__logger.send(text = response.message)

        del self.__requests[user.id]

        return await self.__reset_selection()
    
    async def __rename_playlist_select(self, reaction : Reaction = None, message : Message = None, user : Member = None):
        if message:
            return await message.delete()
        
        self.__requests[user.id].state_function = self.__start_function
    
        if user.id != self.__active_author_id:
            return
        
        if self.__comand_menu.reacted_to_me(reaction = reaction):
            return await self.__requests[user.id].state_function(message = message, reaction = reaction, user = user)
        
        option_index = await self.__selection_menu.get_selection(reaction = reaction)
        if option_index == -1:
            return
        
        playlist_name = self.__selection_menu.get_option(index = option_index)
        self.__requests[user.id].state_value = playlist_name

        self.__requests[user.id].state_function = self.__rename_playlist

        await self.__logger.send(text = f"<@{user.id}> What should **{playlist_name}** be renamed to?")
        return await self.__reset_selection()
    
    async def __rename_playlist(self, reaction : Reaction = None, message : Message = None, user : Member = None):
        if reaction:
            self.__requests[user.id].state_function = self.__start_function
            return await self.__requests[user.id].state_function(message = message, reaction = reaction, user = user)
        
        new_name = message.content
        await message.delete()
        old_name = self.__requests[message.author.id].state_value

        db_response = self.__database.rename_playlist(author_id = message.author.id, old_name = old_name, new_name = new_name)

        del self.__requests[message.author.id]

        return await self.__logger.send(text = db_response.message)
    
    async def __query_search_song(self, reaction : Reaction = None, message : Message = None, user : Member = None):
        if reaction:
            self.__requests[user.id].state_function = self.__start_function
            return await self.__requests[user.id].state_function(message = message, reaction = reaction, user = user)
        
        search_query = message.content
        
        # Garbage fix
        try:
            await message.delete()
        except:
            pass

        tracks = await self.__player_menu.search_query(query = search_query)

        if len(tracks) == 0:
            self.__requests[user.id].state_function = self.__start_function
            return await self.__logger.send(text = f"<@{message.author.id}>  Did not find any songs that match your query.")
        
        options = [track.title for track in tracks]
        self.__searched_tracks = tracks   

        allowed = await self.__make_selection_request(author_id = message.author.id, options = options,  header = f"<@{message.author.id}> Select **Song** to play:")
        if not allowed:
            self.__requests[message.author.id].state_function = self.__start_function
            return
        
        self.__requests[message.author.id].state_function = self.__select_song
        return
    
    async def __select_song(self, reaction : Reaction = None, message : Message = None, user : Member = None):
        if message:
            return await message.delete()
        
        self.__requests[user.id].state_function = self.__start_function
    
        if user.id != self.__active_author_id:
            return
        
        if self.__comand_menu.reacted_to_me(reaction = reaction):
            return await self.__requests[user.id].state_function(message = message, reaction = reaction, user = user)
        
        option_index = await self.__selection_menu.get_selection(reaction = reaction)
        if option_index == -1:
            return
        
        track = self.__searched_tracks[option_index]

        queued = await self.__player_menu.queue_track(track = track, user = user)
        await self.__logger.send(text = f"<@{user.id}>  Added song to queue." if queued else f"<@{user.id}>  Join a voice channel")

        return await self.__reset_selection()


    async def __player_reaction(self, reaction : Reaction = None, user : Member = None):
        if reaction.emoji not in self.__player_menu.get_reactions():
            return
        
        voice_channel = self.__player_menu.get_voice_channel()
        if voice_channel is None:
            return await self.__logger.send(text = f"<@{user.id}> Nothing is playing.")
        
        if not getattr(user.voice, 'channel', None):
            return await self.__logger.send(text = f"<@{user.id}> You are not in a voice channel.")
        
        if user.voice.channel.id != voice_channel.id:
            return await self.__logger.send(text = f"<@{user.id}> You are not in the same voice channel as me.")
        
        if reaction.emoji == "⏮":
            return await self.__player_menu.previous()

        if reaction.emoji == "⏸":
            return await self.__player_menu.pause()
        
        if reaction.emoji == "▶":
            return await self.__player_menu.resume()
        
        if reaction.emoji =="⏭":
            return await self.__player_menu.skip()
        
        if reaction.emoji =="⏹":
            return await self.__player_menu.stop()
        
        if reaction.emoji =="🔄":
            return await self.__player_menu.restart()
        
        if reaction.emoji =="🔀":
            self.__player_menu.shuffle()
            return await self.__logger.send(text = f"<@{user.id}> Shuffled queue.")
        
        if reaction.emoji =="❌":
            playlists = self.__database.get_playlists(author_id = user.id)

            if len(playlists) == 0:
                return await self.__logger.send(f"<@{user.id}> You have no playlists.")
            
            playlist_names = [playlist.name for playlist in playlists]

            allowed = await self.__make_selection_request(author_id = user.id, options = playlist_names, header = f"<@{user.id}> Select **Playlist** to delete song from:")

            if not allowed:
                return            
            
            track = self.__player_menu.get_current_track()
            video_id = track.thumbnail.split("/")[-2]
            self.__requests[user.id] = Request(author_id = user.id, state_function = self.__delete_song_from_playlist, state_value = video_id)
            return
        if reaction.emoji =="💿":
            playlists = self.__database.get_playlists(author_id = user.id)

            if len(playlists) == 0:
                return await self.__logger.send(f"<@{user.id}> You have no playlists.")
            
            playlist_names = [playlist.name for playlist in playlists]

            allowed = await self.__make_selection_request(author_id = user.id, options = playlist_names, header = f"<@{user.id}> Select **Playlist** to add song to:")

            if not allowed:
                return            
            
            track = self.__player_menu.get_current_track()
            video_id = track.thumbnail.split("/")[-2]
            self.__requests[user.id] = Request(author_id = user.id, state_function = self.__add_song_to_playlist, state_value = video_id)
            return
        
        if reaction.emoji =="ℹ️":
            track = self.__player_menu.get_current_track()
            if track is None:
                return await self.__logger.send(text = f"<@{user.id}> Not playing anything.")
            
            message = f"**Title : ** {track.title}\n**Author : ** {track.author}\n**Duration : ** {str(timedelta(milliseconds = track.length))}"
            return await self.__logger.send(text = message)
        
        if reaction.emoji == "🇭":
            tracks = self.__player_menu.get_history_tracks()
            if len(tracks) == 0:
                return await self.__logger.send(text = f"<@{user.id}> No past songs to show.")
            tracks = reversed(tracks[-10:])
            message = ""
            for track in tracks:
                message += f"> {track.title}\n"
            return await self.__logger.send(text = message)

        if reaction.emoji == "🇶":
            tracks = self.__player_menu.get_queued_tracks()
            if len(tracks) == 0:
                return await self.__logger.send(text = f"<@{user.id}> No songs queued.")
            tracks = tracks[:10]
            message = ""
            for track in tracks:
                message += f"{track.title}\n"
            return await self.__logger.send(text = message)

    async def __add_song_to_playlist(self, reaction : Reaction = None, message : Message = None, user : Member = None):
        if message:
            return await message.delete()
        
        if user.id != self.__active_author_id:
            self.__requests[user.id].state_function = self.__start_function
            return
        
        if self.__comand_menu.reacted_to_me(reaction = reaction):
            await self.__reset_selection()
            self.__requests[user.id].state_function = self.__start_function
            return await self.__requests[user.id].state_function(message = message, reaction = reaction, user = user)
        
        option_index = await self.__selection_menu.get_selection(reaction = reaction)
        if option_index == -1:
            return
        
        playlist_name = self.__selection_menu.get_option(index = option_index)
        video_id = self.__requests[user.id].state_value
        
        response = self.__database.add_song_to_playlist(autor_id = user.id, playlist_name = playlist_name, video_id = video_id)
        await self.__logger.send(text = response.message)

        del self.__requests[user.id]

        return await self.__reset_selection()
    
    async def __delete_song_from_playlist(self, reaction : Reaction = None, message : Message = None, user : Member = None):
        if message:
            return await message.delete()
        
        if user.id != self.__active_author_id:
            self.__requests[user.id].state_function = self.__start_function
            return
        
        if self.__comand_menu.reacted_to_me(reaction = reaction):
            await self.__reset_selection()
            self.__requests[user.id].state_function = self.__start_function
            return await self.__requests[user.id].state_function(message = message, reaction = reaction, user = user)
        
        option_index = await self.__selection_menu.get_selection(reaction = reaction)
        if option_index == -1:
            return
        
        playlist_name = self.__selection_menu.get_option(index = option_index)
        video_id = self.__requests[user.id].state_value
        
        response = self.__database.delete_song_from_playlist(autor_id = user.id, playlist_name = playlist_name, video_id = video_id)
        await self.__logger.send(text = response.message)

        del self.__requests[user.id]

        return await self.__reset_selection()
    
    async def __play_playlist(self, reaction : Reaction = None, message : Message = None, user : Member = None):
        if message:
            return await message.delete()
        
        self.__requests[user.id].state_function = self.__start_function
    
        if user.id != self.__active_author_id:
            return
        
        if self.__comand_menu.reacted_to_me(reaction = reaction):
            return await self.__requests[user.id].state_function(message = message, reaction = reaction, user = user)
        
        option_index = await self.__selection_menu.get_selection(reaction = reaction)
        if option_index == -1:
            return
        
        playlist_name = self.__selection_menu.get_option(index = option_index)

        video_ids = self.__database.get_songs_from_playlist(author_id = user.id, playlist_name = playlist_name)

        tracks = []
        for video_id in video_ids:
            track = await self.__player_menu.get_track_from_video_id(video_id = video_id)
            if track is None:
                await self.__logger.send(text = f"<@{user.id}> Song video is unavailable from youtube : {video_id}")
                continue

            tracks.append(track)

        for track in tracks:
            queued = await self.__player_menu.queue_track(track = track, user = user)
            if not queued:
                await self.__logger.send(text = f"<@{user.id}> Join a voice channel.")

        return await self.__reset_selection()
    

