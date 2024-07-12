from discord.ext import commands
from discord import Message, Reaction, Member
from cogs.music.control import Control
from cogs.music.database import Database

from cogs.music.logger import Logger

class MusicServer:
    def __init__(self):
        self.__initialized = False
        self.__logger : Logger = None
        self.__database : Database = None
        self.__control : Control = None

    async def setup(self, ctx : commands.Context):        
        text_channels = ctx.guild.text_channels
        channel_names = [str(channel) for channel in text_channels]
        if 'music-bot' not in channel_names:
            text_channel = await ctx.guild.create_text_channel('music-bot')
        else:
            text_channel = text_channels[channel_names.index('music-bot')]
        
        await text_channel.purge()

        self.__database = Database()
               
        self.__logger = Logger(text_channel = text_channel)
        await self.send_notification("Initializing, please wait...")
        
        self.__control = Control(text_channel = text_channel, database = self.__database, logger = self.__logger)
        await self.__control.setup()

        await self.__logger.clear()
        self.__initialized = True

    async def process_message(self, message : Message):
        if not self.__initialized:
            return
        
        return await self.__control.process_input(message = message)
        

    async def process_reaction(self, reaction : Reaction, user : Member):
        if not self.__initialized:
            return
        
        if self.__control.reacted_to_me(reaction = reaction):
            return await self.__control.process_input(reaction = reaction, user = user)

    async def send_notification(self, text : str, embed = None):
        await self.__logger.send(text = text, embed = embed)

    async def song_ended_notification(self):
        await self.__control.song_ended_notification()
