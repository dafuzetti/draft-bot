from discord import app_commands
import discord
import pandas
import data_base
import functions
from decouple import config

my_secret = config("TOKEN")
intents = discord.Intents.default()
client = discord.Client(intents=intents)
bot = app_commands.CommandTree(client)


@ bot.command(name='newevent', description='Create new event. teams: 2-A vs B or 0-Individual. Type: 0-all possible matches')
async def newevent(ctx, teams: int = 2, type: int = 0):
    await ctx.response.defer()
    data_base.new_event(ctx, teams, type)
    embed = functions.print_event(ctx)
    await ctx.followup.send(embed=embed, ephemeral=True)


@ bot.command(name='play', description='Join the event.')
async def play(ctx, team: str = None):
    await ctx.response.defer()
    functions.add_players(ctx, team, ctx.user)
    embed = functions.print_event(ctx)
    await ctx.followup.send(embed=embed, ephemeral=True)


@ bot.command(name='team',
              description='Add up to 4 players to a team for the event.')
async def team(ctx, team: str = None, p1: discord.User = None,
               p2: discord.User = None, p3: discord.User = None,
               p4: discord.User = None):
    await ctx.response.defer()
    functions.add_players(ctx, team, p1, p2, p3, p4)
    embed = functions.print_event(ctx)
    await ctx.followup.send(embed=embed, ephemeral=True)


@ bot.command(name='players', description='Add up to 8 players to the event.')
async def players(ctx, p1: discord.User, p2: discord.User = None,
                  p3: discord.User = None, p4: discord.User = None,
                  p5: discord.User = None, p6: discord.User = None,
                  p7: discord.User = None, p8: discord.User = None):
    await ctx.response.defer()
    functions.add_players(ctx, None, p1, p2, p3, p4, p5, p6, p7, p8)
    embed = functions.print_event(ctx)
    await ctx.followup.send(embed=embed, ephemeral=True)


@ bot.command(name='event', description='Manage current event.')
async def event(ctx, action: str = '', draftdate: str = None):
    await ctx.response.defer()
    draft = None
    if action.lower() == 'start':
        functions.start(ctx)
    elif action.lower() == 'close':
        data_base.close_event(ctx)
    elif action.lower() == 'clear':
        data_base.clear_event(ctx)
    elif action.lower() == 'rdm':
        draft = None
    embed = functions.print_event(ctx)
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


@ bot.command(name='history', description='Draft history details.')
async def history(ctx, draft: int = None):
    await ctx.response.defer()
    embed = functions.print_event(ctx, draft)
    await ctx.followup.send(embed=embed, ephemeral=True)


@ bot.command(name='score', description='All time scoreboard for the channel!')
async def score(ctx):
    dataFrame = data_base.read_history(ctx)
    dt = pandas.DataFrame()

    dt = dataFrame.groupby(['Player', 'Date']).agg(
        {'Victory': 'mean', 'Match': ['count', 'sum']}).reset_index()
    dt.columns = [col[0] + '_' + col[1] if col[1] else col[0]
                  for col in dt.columns]
    dt = dt.groupby(['Player']).agg(
        {'Date': 'count', 'Victory_mean': 'sum', 'Match_sum': 'sum', 'Match_count': 'sum'}).reset_index()
    dt = dt.rename(
        columns={"Date": "T(D)",
                 "Victory_mean": "Draft Wins",
                 "Match_count": "T(M)",
                 "Match_sum": "Match Wins"})
    dt = dt.reindex(
        columns=['Draft Wins', 'T(D)', 'Match Wins', 'T(M)', 'Player'])
    dt['Draft Wins'] = dt['Draft Wins'].astype(int)
    dt.sort_values(['Draft Wins', 'Match Wins', 'Player'],
                   axis=0, inplace=True, ascending=False,
                   na_position='first')

    embed = discord.Embed(title="__**Scoreboard:**__", color=0x03f8fc)
    pos = 0
    list = dt.values.tolist()
    for match in list:
        pos = pos + 1
        embed.add_field(name=f'Rank: {pos}',
                        value=f'Player: {match[4]}\nDraft: {match[0]}/{match[1]} - {match[0]*100//match[1]}%\nMatch: {match[2]}/{match[3]} - {match[2]*100//match[3]}%', inline=True)
    await ctx.response.send_message(embed=embed)


@ bot.command(name='dates', description='History of draft\'s dates list.')
async def dates(ctx):
    hist = data_base.read_history(ctx)
    embed = discord.Embed(title="__**Draft**__", color=0x03f8fc)
    list = hist['Date'].unique()
    count = 0
    dates = ''
    for match in list:
        count = count + 1
        dates = dates + str(count) + '-' + match + '\n'

    embed.add_field(name='Dates', value=dates, inline=False)
    await ctx.response.send_message(embed=embed)


@ bot.command(name='ids', description='History of draft\'s dates list.')
async def ids(ctx):
    hist = data_base.read_history(ctx)
    embed = discord.Embed(
        title=f"__**Channel id:{ctx.guild.id}**__", color=0x03f8fc)
    list = hist['Player'].unique()
    count = 0
    dates = ''
    for match in list:
        count = count + 1
        dates = dates + str(count) + '-' + match + ': ' + match[2:~0] + '\n'

    embed.add_field(name='Players', value=dates, inline=False)
    await ctx.response.send_message(embed=embed)


@ client.event
async def on_ready():
    await client.change_presence()
    await bot.sync()
    print('Running')


client.run(my_secret)
