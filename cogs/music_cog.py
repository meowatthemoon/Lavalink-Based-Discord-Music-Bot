import wavelink
import discord
from discord.ext import commands
from cogs.music.music_server import MusicServer
from config import LAVALINK_HOST, LAVALINK_PORT, LAVALINK_PASSWORD

class MusicCog(commands.Cog):
    def __init__(self, bot : commands.Bot):
        self.bot : commands.Bot = bot
        self.bot.loop.create_task(self.node_connect())

        self.servers : dict = {}

     #-------------- Wave link block ----------------------------------#
    async def node_connect(self):
        await self.bot.wait_until_ready()

        node: wavelink.Node = wavelink.Node(
            uri = f"http://{LAVALINK_HOST}:{LAVALINK_PORT}", 
            password = LAVALINK_PASSWORD
        )
        await wavelink.Pool.connect(client = self.bot, nodes = [node])

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node : wavelink.Node):
        print(f'Bot and wavelink node ready : {discord.__version__}')

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload):
        server = await self.__get_server_by_id(server_id = payload.player.guild.id)
        await server.song_ended_notification()

    #-------------- Servers -------------------------------------------#
    @commands.command(pass_context=True, aliases=['*'])
    async def setup(self, ctx : commands.Context):
        await self.__get_server(ctx = ctx)

    async def __get_server(self, ctx : commands.Context) -> MusicServer:
        server_id = str(ctx.guild.id)
        if server_id not in self.servers.keys():
            self.servers[server_id] = MusicServer()
            await self.servers[server_id].setup(ctx = ctx)
        return self.servers[server_id]
    
    async def __get_server_by_id(self, server_id : int) -> MusicServer:
        server_id = str(server_id)
        assert server_id in self.servers.keys()

        return self.servers[server_id]
    
    # ---------------------- PROCESSING --------------------------#
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction : discord.Reaction, user : discord.Member):
        if user.bot:
            return
        server = await self.__get_server_by_id(server_id = reaction.message.guild.id)
        await server.process_reaction(reaction = reaction, user = user)
        await reaction.remove(user = user)

    @commands.Cog.listener()
    async def on_message(self, message : discord.Message):
        if message.author.bot:
            return
        server = await self.__get_server_by_id(server_id = message.guild.id)
        await server.process_message(message = message)


async def setup(bot):
    await bot.add_cog(MusicCog(bot))
