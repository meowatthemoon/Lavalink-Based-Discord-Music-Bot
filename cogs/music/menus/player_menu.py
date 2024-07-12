from discord import Member, Message, TextChannel, VoiceChannel, Reaction
import wavelink

from cogs.music.menus.menu import Menu

from wavelink import Playable, Player, tracks

from cogs.music.queue import Queue


class PlayerMenu:
    def __init__(self, text_channel : TextChannel):
        self.__reactions = ["⏮", "⏸", "▶", "⏭", "⏹", "🔄", "🔀", "❌","💿", "ℹ️", "🇭", "🇶"] # "🎵"
        self.__text_channel : TextChannel = text_channel
        self.__display_message : Message = None

        self.__queue = Queue()

        self.__is_playing = False
        self.__voice_channel : VoiceChannel = None
        self.__vc : Player = None

    async def display(self, text : str = None):
        if text is None:
            text = 'Nothing playing.'

        if self.__display_message is not None:
            await self.__display_message.edit(content = text)
            return
        
        self.__display_message = await self.__text_channel.send(text)
        for reaction in self.__reactions:
            await self.__display_message.add_reaction(reaction)

    def reacted_to_me(self, reaction : Reaction) -> bool:
        return reaction.message.id == self.__display_message.id

    async def search_query(self, query : str) -> wavelink.Search:
        return await wavelink.Playable.search(query)
    
    async def queue_track(self, track : tracks.Playable, user : Member) -> bool:
        joined = await self.join_voice_channel(user = user)
        if not joined:
            return False
     
        added = self.__queue.add_track(track)
        print(f"[DEBUG] Added {track.title} to queue" if added else "Failed to add song to queue")

        return await self.__play()
        
    
    async def play_next_track(self) -> bool:
        self.__is_playing = False
        if self.__queue.is_empty():
            return False

        print(f"[DEBUG] Stopped playing {self.__queue.get_current_track().title}")
        return await self.__play()
        

    async def join_voice_channel(self, user : Member) -> bool:
        if not getattr(user.voice, 'channel', None):
            return False
        
        new_channel = user.voice.channel
        if self.__voice_channel is None or new_channel.id != self.__voice_channel.id:
            self.__voice_channel = new_channel
            self.__vc : Player = await self.__voice_channel.connect(cls = Player)

        return True
    
    async def __play(self) -> bool:
        if self.__is_playing:
            return True
        
        
        track = self.__queue.get_next_track()

        url = track.uri
        await self.display(text = url)
        print(f"[DEBUG] Playing {track.title} | {url}")
        await self.__vc.play(track)
        self.__is_playing = True

        return True
    
    def get_current_track(self) -> tracks.Playable:
        return self.__queue.get_current_track()
    
    def get_history_tracks(self) -> list[tracks.Playable]:
        return self.__queue.get_history_tracks()
    
    def get_queued_tracks(self) -> list[tracks.Playable]:
        return self.__queue.get_queued_tracks()

    def get_reactions(self) -> list[str]:
        return self.__reactions
    
    async def get_track_from_video_id(self, video_id : str) -> tracks.Playable:
        url = f"https://www.youtube.com/watch?v={video_id}"
        tracks = await Playable.search(url)
        
        # Not sure if this is enough for when a video is deleted/privated, maybe a try catch is better, time will tell when a song video is deleted
        if len(tracks) == 0:
            return None
        
        return tracks[0]
    
    def get_voice_channel(self) -> VoiceChannel:
        return self.__voice_channel
    
    async def pause(self):
        if self.__vc is not None:
            await self.__vc.pause()

    async def previous(self):
        if self.__is_playing and len(self.__queue.get_history_tracks()) > 0:
            self.__queue.skip_by(jump = -2)
            await self.__vc.stop()
            self.__is_playing = False

    async def restart(self):
        if self.__is_playing:
            self.__queue.skip_by(jump = -1)
            await self.__vc.stop()
            self.__is_playing = False

    async def resume(self):
        if self.__vc is not None:
            await self.__vc.resume()

    def shuffle(self):
        self.__queue.shuffle()
    
    async def skip(self):
        if self.__is_playing:
            await self.__vc.stop()
            self.__is_playing = False

    async def stop(self):
        self.__queue.reset()

        if self.__vc is not None:
            await self.__vc.stop()
            await self.__vc.disconnect()

        self.__is_playing : bool = False
        self.__voice_channel : VoiceChannel = None
        self.__vc : Player = None

        await self.display(text = "Not playing anything.")
