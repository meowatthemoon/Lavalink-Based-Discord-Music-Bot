from discord import TextChannel, Message, Embed
from discord.errors import NotFound


class Logger:
    def __init__(self, text_channel : TextChannel):
        self.__text_channel : TextChannel = text_channel
        self.__last_notification : Message = None

    async def send(self, text : str, embed : Embed = None):
        await self.clear()
        
        text = "".join([f"> {line}\n" for line in text.split("\n")])

        self.__last_notification = await self.__text_channel.send(f"{text}", embed = embed)

    async def clear(self):
        if self.__last_notification is None:
            return
        
        try:
            await self.__last_notification.delete() 
        except NotFound:
            print("Caught exception for some reason.")
            return
