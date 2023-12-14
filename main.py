from discord import app_commands
import discord
import itertools
import pandas
import numpy
import math
import data_base
from datetime import date
from decouple import config

my_secret = config("TOKEN")
intents = discord.Intents.default()
client = discord.Client(intents=intents)
bot = app_commands.CommandTree(client)


@client.event
async def on_guild_join(guild):
    await data_base.folder(guild)


@bot.command(name='score', description='All time scoreboard for the channel!')
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


@ bot.command(name='breakatie',
              description='Add a match to the event when there is a tie.')
async def breakatie(ctx, user1d: discord.User, user2d: discord.User):
    user1 = id_to_usr(user1d.id)
    user2 = id_to_usr(user2d.id)
    event_playes = data_base.read_current(ctx)
    windiff_teamA = windiff_a(event_playes)
    if windiff_teamA == 0:
        objs = event_playes.loc[event_playes['Team A'].isin(
            [user1, user2]) & event_playes['Team B'].isin([user1, user2])]
        if len(objs) == 1:
            objs.at[objs.index[0], 'W-A'] = '-'
            objs.at[objs.index[0], 'W-B'] = '-'
            event_playes = pandas.concat(
                [event_playes, objs], ignore_index=True)
            await data_base.save_current(ctx, event_playes)
    await print_event(ctx)


@ bot.command(name='play', description='Join the event.')
async def play(ctx, team: str = None):
    event_playes = data_base.read_players(ctx)
    event_playes = add_player(event_playes, ctx.user.id, team)
    await data_base.save_players(ctx, event_playes)
    await print_event(ctx)


@ bot.command(name='team',
              description='Add up to 4 players to a team for the event.')
async def team(ctx, team: str = None, p1: discord.User = None,
               p2: discord.User = None, p3: discord.User = None,
               p4: discord.User = None):
    await add_players(ctx, team, p1, p2, p3, p4)


@ bot.command(name='players', description='Add up to 8 players to the event.')
async def players(ctx, p1: discord.User, p2: discord.User = None,
                  p3: discord.User = None, p4: discord.User = None,
                  p5: discord.User = None, p6: discord.User = None,
                  p7: discord.User = None, p8: discord.User = None):
    await add_players(ctx, None, p1, p2, p3, p4, p5, p6, p7, p8)


@ bot.command(name='lose', description='Report a match that you lose.')
async def lose(ctx, player_win: discord.User, gameloss: int = 0):
    await resultado(ctx, id_to_usr(player_win.id), id_to_usr(ctx.user.id), gameloss)


@ bot.command(name='win', description='Report a match that you won.')
async def win(ctx, player_lost: discord.User, gameloss: int = 0):
    await resultado(ctx, id_to_usr(ctx.user.id), id_to_usr(player_lost.id), gameloss)


@ bot.command(name='result', description='Report the result of a match.')
async def result(ctx, player_win: discord.User,
                 player_lose: discord.User, gameloss: int = 0):
    await resultado(ctx, id_to_usr(player_win.id), id_to_usr(player_lose.id), gameloss)


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


@bot.command(name='history', description='Draft history details.')
async def history(ctx, draft: int = None):
    await history_run(ctx, draft)


@ bot.command(name='event', description='Manage current event.')
async def event(ctx, action: str = '', draftdate: str = None):
    data = None
    ifclose = False
    if action.lower() == 'start':
        if draftdate is None:
            draftdate = date.today().strftime("%d/%m/%Y")
        data = await start(ctx, draftdate)
        await print_event(ctx, data)
    elif action.lower() == 'close':
        ifclose = await close(ctx)
        if ifclose:
            await history_run(ctx)
        else:
            await print_event(ctx, data)
    elif action.lower() == 'clear':
        await clear(ctx)
        await print_event(ctx)
    elif action.lower() == 'rdm':
        data = event_rdm(ctx)
        await print_event(ctx, data)
    else:
        await print_event(ctx)


async def history_run(ctx, draft: int = None):
    hist = data_base.read_history(ctx)
    draftdate = ''
    if draft is None:
        last_row = hist.iloc[-1]
        draftdate = last_row['Date']
    else:
        draftdate = hist['Date'].unique()[draft-1]
    embed = discord.Embed(title=f"__**{draftdate}**__", color=0x03f8fc)
    condition = (hist['Date'] == draftdate)
    hist = hist[condition]
    list = hist.values.tolist()
    players = hist.groupby(['Player']).agg(
        {'Victory': 'mean', 'Match': 'sum'}).reset_index()

    playersA = ''
    playersB = ''
    totalA = 0
    totalB = 0
    for play in players.values.tolist():
        if play[1] == 1:
            totalA = totalA + play[2]
            playersA = playersA + str(play[0]) + '(' + str(play[2]) + ') '
        else:
            playersB = playersB + str(play[0]) + '(' + str(play[2]) + ') '
            totalB = totalB + play[2]

    marchlist = ''
    for match in list:
        if match[1] == 1:
            marchlist = marchlist + \
                str(match[2]) + ' ' + str(match[4]) + '-' + \
                str(match[6]) + ' ' + str(match[5]) + '\n'
    embed.add_field(
        name=f'Winners: {totalA}', value=playersA, inline=False)
    embed.add_field(
        name=f'Less winners: {totalB}', value=playersB, inline=False)
    embed.add_field(name='Matches: ' + str(totalA + totalB),
                    value=marchlist, inline=False)
    await ctx.response.send_message(embed=embed)


async def event_rdm(ctx):
    df = data_base.read_players(ctx)
    half_size = len(df) // 2
    random_indices = numpy.random.choice(df.index, half_size, replace=False)
    df.loc[random_indices, 'Team'] = 'A'
    df.loc[~df.index.isin(random_indices), 'Team'] = 'B'
    await data_base.save_players(ctx, df)
    return df


async def clear(ctx):
    await data_base.save_players(ctx, data_base.dataframe_players())
    await data_base.save_current(ctx, data_base.dataframe_current())
    data_base.read_start(ctx, date.today().strftime("%d/%m/%Y"))


async def start(ctx, date):
    data_base.read_start(ctx, date)
    df = data_base.read_players(ctx)
    counts = df['Team'].value_counts()
    if len(df) in [4, 6, 8] and counts.nunique() == 1 and len(counts) == 2:
        TeamA = df[df['Team'] == 'A']
        TeamB = df.drop(TeamA.index)
        Mlist = itertools.product(
            TeamA['Player'].tolist(), TeamB['Player'].tolist())
        df = pandas.DataFrame(Mlist, columns=['Team A', 'Team B'])
        df.insert(1, 'W-A', '-')
        df.insert(3, 'W-B', '-')
        await data_base.save_current(ctx, df)
    return df


async def close(ctx):
    current = data_base.read_current(ctx)
    current = current[(current['W-A'] != '-') & (current['W-B'] != '-')]
    windiff_teamA = windiff_a(current)
    fechou = False
    if windiff_teamA != 0:
        fechou = True
        history = data_base.read_history(ctx)
        draftID = data_base.read_start(ctx)
        teamA = current
        teamB = current
        teamA = teamA.rename(
            columns={"Team A": "Player", "Team B": "Opponent",
                     "W-B": "Game-Lose", "W-A": "Game-Win"})
        teamB = teamB.rename(
            columns={"Team B": "Player", "Team A": "Opponent",
                     "W-A": "Game-Lose", "W-B": "Game-Win"})
        if (windiff_teamA > 0):
            teamA.insert(0, 'Victory', 1)
            teamB.insert(0, 'Victory', 0)
        else:
            teamA.insert(0, 'Victory', 0)
            teamB.insert(0, 'Victory', 1)
        current = pandas.concat([teamA, teamB], ignore_index=True)
        current['Match'] = numpy.where(current['Game-Win'] == 2, 1, 0)
        current.insert(0, 'Date', draftID)
        current = current.reindex(
            columns=['Date', 'Victory', 'Player', 'Match',
                     'Game-Win', 'Opponent', 'Game-Lose'])
        current.sort_values(['Victory', 'Player'],
                            axis=0, inplace=True, ascending=False,
                            na_position='first')
        history = pandas.concat([history, current], ignore_index=True)
        await data_base.save_history(ctx, history)
        await send_file(ctx)
        await clear(ctx)
    return fechou


async def add_players(ctx, team, p1: discord.User, p2: discord.User = None,
                      p3: discord.User = None, p4: discord.User = None,
                      p5: discord.User = None, p6: discord.User = None,
                      p7: discord.User = None, p8: discord.User = None):
    event_playes = data_base.read_players(ctx)
    list = []
    list.append(p1)
    list.append(p2)
    list.append(p3)
    list.append(p4)
    list.append(p5)
    list.append(p6)
    list.append(p7)
    list.append(p8)
    for player in list:
        if player is not None:
            event_playes = add_player(event_playes, player.id, team)
    await data_base.save_players(ctx, event_playes)
    await print_event(ctx, event_playes)


def add_player(event_playes, userdata: str, team=None):
    if userdata is not None and len(event_playes) < 8:
        user = id_to_usr(userdata)
        condition = event_playes['Player'] == user
        event_playes = event_playes.drop(event_playes[condition].index)
        if team not in ('A', 'B'):
            size = len(event_playes)
            if size == 0:
                team = 'A'
            elif size == 1:
                team = 'B'
            else:
                team = event_playes['Team'].value_counts().idxmin()
        df2 = data_base.dataframe_players([[user, team]])
        event_playes = pandas.concat([event_playes, df2], ignore_index=True)
    return event_playes


async def send_file(ctx):
    # file_path = filenames(ctx, FILE_HISTORY)
    # try:
    #    target_channel = discord.utils.get(
    #        ctx.guild.channels, name='db')
    #    with open(file_path, 'rb') as file:
    #        file_data = discord.File(file)
    #        await target_channel.send(file=file_data)
    # except Exception:
    return


def windiff_a(currentin):
    current = currentin
    current['W-A'] = pandas.to_numeric(current['W-A'], errors='coerce')
    current['W-B'] = pandas.to_numeric(current['W-B'], errors='coerce')

    diff = (current[current['W-A'] == 2]['Team A'].count()) - \
        (current[current['W-B'] == 2]['Team B'].count())
    diff2 = (current[current['W-A'] == 1]['Team A'].count()) - \
        (current[current['W-B'] == 1]['Team B'].count())
    return (diff * 100) + diff2


async def print_event(ctx, data=None):
    if data is None:
        dt = data_base.read_current(ctx)
    else:
        dt = data
    if len(dt) > 0 and dt.shape[1] > 2:
        await print_event_started(ctx, dt)
    else:
        await print_players(ctx)


async def print_players(ctx):
    dt = data_base.read_players(ctx)
    embed = discord.Embed(title="__**Players**__", color=0x03f8fc)
    list = dt.values.tolist()
    playersA = ''
    playersB = ''
    for match in list:
        if str(match[1]) == 'A':
            playersA = playersA + match[0] + ' '
        if str(match[1]) == 'B':
            playersB = playersB + match[0] + ' '

    embed.add_field(name='Team A', value=playersA, inline=False)
    embed.add_field(name='Team B', value=playersB, inline=False)
    await ctx.response.send_message(embed=embed)


async def print_event_started(ctx, dt):
    name = data_base.read_start(ctx)
    embed = discord.Embed(title=f"__**{name[:10]}**__", color=0x03f8fc)
    list = dt.values.tolist()
    count = len(list)
    matches = ''
    playersA = ''
    playersB = ''
    winA = 0
    winB = 0
    pos = 0
    nrp = math.sqrt(count)
    toadd = 1
    emjA = ':family:'
    emjB = ':family:'
    for match in list:
        pos = pos + 1
        if str(match[1]) == '2':
            winA = winA + 1
        if str(match[3]) == '2':
            winB = winB + 1
        if pos == toadd:
            playersA = playersA + match[0]
            playersB = playersB + match[2]
            toadd = toadd + nrp + 1
        matches = matches + str(match[0]) + ' ' + str(match[1]) + \
            '-' + str(match[3]) + ' ' + str(match[2]) + '\n'

    if winA > winB:
        emjA = ':airplane:'
        emjB = ':poo:'
    if winB > winA:
        emjA = ':poo:'
        emjB = ':airplane:'
    if winA > count/2:
        emjA = ':trophy:'
        emjB = ':skull:'
    if winB > count/2:
        emjA = ':skull:'
        emjB = ':trophy:'
    embed.add_field(name='Team A ' + str(emjA),
                    value=f'Players: {playersA}\nWin: {winA}', inline=False)
    embed.add_field(name='Team B ' + str(emjB),
                    value=f'Players: {playersB}\nWin: {winB}', inline=False)
    embed.add_field(name=f'Pairings: {winA + winB}/{count}',
                    value=matches, inline=False)
    await ctx.response.send_message(embed=embed)


def id_to_usr(id):
    return '<@'+str(id)+'>'


async def resultado(ctx, userW, userL, loss=0):
    gameloss = 0
    if loss != 0:
        gameloss = 1
    df = data_base.read_current(ctx)
    objs = df.loc[df['Team A'].isin(
        [userW, userL]) & df['Team B'].isin([userW, userL])]
    matches = len(objs)
    if matches > 0:
        teamA = (len(objs.loc[objs['Team A'] == userW]) > 0)
        if teamA:
            df.at[objs.index[matches-1], 'W-A'] = 2
            df.at[objs.index[matches-1], 'W-B'] = gameloss
        else:
            df.at[objs.index[matches-1], 'W-A'] = gameloss
            df.at[objs.index[matches-1], 'W-B'] = 2
        await data_base.save_current(ctx, df)
    await print_event(ctx)


@ client.event
async def on_ready():
    await client.change_presence()
    await bot.sync()
    print('Running')


client.run(my_secret)
