from discord import app_commands
import discord
import data_base
import functions
from decouple import config

my_secret = config("TOKEN")
intents = discord.Intents.default()
client = discord.Client(intents=intents)
bot = app_commands.CommandTree(client)


@ bot.command(name='newevent', description='Create new event. teams: 2-A vs B or 0-Individual. Type: 0-all possible matches')
async def newevent(ctx):
    teams: int = 2
    type: int = 0
    await ctx.response.defer()
    data_base.new_event(ctx, teams, type)
    embed = functions.print_event(ctx)
    await ctx.followup.send(embed=embed, ephemeral=True)


@ bot.command(name='play', description='Join the event.')
async def play(ctx):
    await ctx.response.defer()
    functions.add_players(ctx, False, ctx.user)
    embed = functions.print_event(ctx)
    await ctx.followup.send(embed=embed, ephemeral=True)


@ bot.command(name='team',
              description='Add up to 4 players to a team for the event.')
async def team(ctx, p1: discord.User = None,
               p2: discord.User = None, p3: discord.User = None,
               p4: discord.User = None):
    await ctx.response.defer()
    functions.add_players(ctx, True, p1, p2, p3, p4)
    embed = functions.print_event(ctx)
    await ctx.followup.send(embed=embed, ephemeral=True)


@ bot.command(name='players', description='Add up to 8 players to the event.')
async def players(ctx, p1: discord.User, p2: discord.User = None,
                  p3: discord.User = None, p4: discord.User = None,
                  p5: discord.User = None, p6: discord.User = None,
                  p7: discord.User = None, p8: discord.User = None):
    await ctx.response.defer()
    functions.add_players(ctx, False, p1, p2, p3, p4, p5, p6, p7, p8)
    embed = functions.print_event(ctx)
    await ctx.followup.send(embed=embed, ephemeral=True)


@ bot.command(name='event', description='Manage current event.')
async def event(ctx, action: str = '', draftdate: str = None):
    await ctx.response.defer()
    event_id = None
    if action.lower() == 'start':
        functions.start(ctx)
    elif action.lower() == 'close':
        event_id = data_base.close_event(ctx)
    elif action.lower() == 'clear':
        data_base.clear_event(ctx)
    embed = functions.print_event(ctx, event_id)
    await ctx.followup.send(embed=embed, ephemeral=True)


@ bot.command(name='lose', description='Report a match that you lose.')
async def lose(ctx, player_win: discord.User, gameloss: int = 0):
    await ctx.response.defer()
    functions.resultado(ctx, player_win.mention, ctx.user.mention, gameloss)
    embed = functions.print_event(ctx)
    await ctx.followup.send(embed=embed, ephemeral=True)


@ bot.command(name='win', description='Report a match that you won.')
async def win(ctx, player_lost: discord.User, gameloss: int = 0):
    await ctx.response.defer()
    functions.resultado(ctx, ctx.user.mention, player_lost.mention, gameloss)
    embed = functions.print_event(ctx)
    await ctx.followup.send(embed=embed, ephemeral=True)


@ bot.command(name='result', description='Report the result of a match.')
async def result(ctx, player_win: discord.User,
                 player_lose: discord.User, gameloss: int = 0):
    await ctx.response.defer()
    functions.resultado(ctx, player_win.mention, player_lose.mention, gameloss)
    embed = functions.print_event(ctx)
    await ctx.followup.send(embed=embed, ephemeral=True)


@ bot.command(name='history', description='Event list or history details for specific events.')
async def history(ctx, event_id: int = None, channel: bool = False):
    await ctx.response.defer()
    if event_id is None:
        embed = functions.print_history(ctx, channel)
    else:
        embed = functions.print_event(ctx, event_id)
    await ctx.followup.send(embed=embed, ephemeral=True)


@ bot.command(name='ids', description='History of draft\'s dates list.')
async def ids(ctx):
    await ctx.response.defer()
    embed = discord.Embed(
        title=f"__**Server ID: {ctx.guild.id}**__", color=0x03f8fc)
    count = 0
    players = ''
    list = data_base.player_history(ctx)
    for player in list:
        count = count + 1
        players = players + str(count) + '-' + player[0] + ' (' + str(
            player[1]) + '): ' + str(player[0])[2:~0] + '\n'

    embed.add_field(name='Players', value=players, inline=False)
    await ctx.followup.send(embed=embed, ephemeral=True)


@ bot.command(name='score', description='All time scoreboard for the channel!')
async def score(ctx):
    await ctx.response.defer()
    list = data_base.read_score(ctx)
    embed = discord.Embed(title="__**Scoreboard:**__", color=0x03f8fc)
    pos = 0
    for match in list:
        pos = pos + 1
        embed.add_field(name=f'Rank: {pos}',
                        value=f'Player: {match[4]}\nDraft: {match[0]}/{match[1]} - {match[5]}%\nMatch: {match[2]}/{match[3]} - {match[6]}%', inline=True)
    await ctx.followup.send(embed=embed, ephemeral=True)


@ client.event
async def on_ready():
    await client.change_presence()
    await bot.sync()
    print('Running')


client.run(my_secret)
