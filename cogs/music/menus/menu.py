from discord import Message, Reaction, TextChannel

from cogs.music.utils import emote_from_index, emote_to_index

ITEMS_PER_PAGE = 10

class Menu:
    def __init__(self, text_channel : TextChannel, options : list[str] = [], default_message : str = '', fixed : bool = False):
        self._reactions  = [emote_from_index(index = i) for i in range(min(10, len(options)) if fixed else 10)] 
        self._reactions += ["⬅️", "➡️"]

        self.__text_channel : TextChannel = text_channel
        self.options : list[str] = options
        self.__default_message : str = default_message

        self.__display_message : Message = None
        self.page_idx : int = 0

    def change_options(self, options : list[str]):
        self.options = options

    async def display(self, header : str = ""):        
        content = self.__get_message_content()
        content = f"{header}\n{content}" if header != "" else content

        if self.__display_message is not None:
            await self.__display_message.edit(content = content)
            return
            
        self.__display_message = await self.__text_channel.send(content)
        for reaction in self._reactions:
            await self.__display_message.add_reaction(reaction)
   
    def get_option(self, index : int) -> str:
        if index >= len(self.options):
            return ""
        
        return self.options[index]
    
    def __get_message_content(self) -> str:
        start_idx = self.page_idx * ITEMS_PER_PAGE
        end_idx = min(start_idx + ITEMS_PER_PAGE, len(self.options))

        if len(self.options) == 0:
            return self.__default_message
        
        content = ""
        for i in range(start_idx, end_idx):
            index = i - start_idx
            content += f"{emote_from_index(index = index)} - {self.options[i]}\n"
            
        return content

    def reacted_to_me(self, reaction : Reaction) -> bool:
        return reaction.message.id == self.__display_message.id
    
    async def previous_page(self):
        self.page_idx = max(0, self.page_idx - ITEMS_PER_PAGE)
        await self.display()

    async def next_page(self):
        if self.page_idx + ITEMS_PER_PAGE < len(self.options):
            self.page_idx += ITEMS_PER_PAGE

        await self.display()

    async def get_selection(self, reaction : Reaction) -> int:
        if reaction.emoji not in self._reactions:
            return -1
        
        if reaction.emoji == "⬅️":
            await self.previous_page()
            return -1
        
        if reaction.emoji == "➡️":
            await self.next_page()
            return -1
        
        
        index = self.page_idx + emote_to_index(reaction.emoji)
        if index >= len(self.options):
            return -1
    
        return index
    
