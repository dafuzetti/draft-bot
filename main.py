
from discord.ext import commands
from discord.ext.commands import Bot
import discord
import itertools
import pandas
import numpy
import math
import os
from datetime import datetime
from datetime import date

my_secret = os.environ['TOKEN']
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
FILE_CURRENT = 'current.csv'
FILE_HISTORY = 'history.csv'
FILE_PLAYERS = 'players.csv'
FILE_START = 'start.txt'
EU = 723638398312513586


def filenames(ctx, name):
    folder_path = 'channel_' + str(ctx.guild.id)
    full_path = os.path.join(folder_path, name)
    return str(full_path)


@ bot.command(name='folder')
async def folder(ctx):
    folder_path = 'channel_' + str(ctx.guild.id)
    if not os.path.exists(folder_path):
        full_pathc = os.path.join(folder_path, FILE_CURRENT)
        os.makedirs(folder_path, exist_ok=True)
        with open(full_pathc, 'w') as file:
            file.write('')
        file.close()
        full_pathc = os.path.join(folder_path, FILE_HISTORY)
        with open(full_pathc, 'w') as file:
            file.write('')
        file.close()
        full_pathc = os.path.join(folder_path, FILE_PLAYERS)
        with open(full_pathc, 'w') as file:
            file.write('')
        file.close()
        full_pathc = os.path.join(folder_path, FILE_START)
        with open(full_pathc, 'w') as file:
            file.write('')
        file.close()


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
        dt = read_current(ctx)
    else:
        dt = data
    if len(dt) > 0 and dt.shape[1] > 2:
        await print_event_started(ctx, dt)
    else:
        await print_players(ctx)


async def print_players(ctx):
    dt = read_players(ctx)
    embed = discord.Embed(title=f"__**Players**__", color=0x03f8fc)
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
    await ctx.send(embed=embed)


async def print_event_started(ctx, dt):
    name = read_start(ctx)
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
    embed.add_field(name=f'Team A ' + emjA,
                    value=f'Players: {playersA}\nWin: {winA}', inline=False)
    embed.add_field(name=f'Team B ' + emjB,
                    value=f'Players: {playersB}\nWin: {winB}', inline=False)
    embed.add_field(name=f'Pairings: {winA + winB}/{count}',
                    value=matches, inline=False)
    await ctx.send(embed=embed)


def id_to_usr(id):
    return '<@'+str(id)+'>'


async def resultado(ctx, userW, userL, loss=0):
    gameloss = 0
    if loss != 0:
        gameloss = 1
    df = read_current(ctx)
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
        df.to_csv(filenames(ctx, FILE_CURRENT), sep=',',
                  index=False, encoding='utf-8')
    await print_event(ctx)


@ bot.command(name='lose')
async def lose(ctx, player_win, gameloss=0):
    await resultado(ctx, player_win, id_to_usr(ctx.author.id), gameloss)


@ bot.command(name='win')
async def win(ctx, player_lost, gameloss=0):
    await resultado(ctx, id_to_usr(ctx.author.id), player_lost, gameloss)


@ bot.command(name='result')
async def result(ctx, player_win, player_lose, gameloss=0):
    await resultado(ctx, player_win, player_lose, gameloss)


@ bot.command(name='dates')
async def dates(ctx, draft=None):
    hist = read_history(ctx)
    embed = discord.Embed(title=f"__**Draft**__", color=0x03f8fc)
    list = hist['Date'].unique()
    count = 0
    dates = ''
    for match in list:
        count = count + 1
        dates = dates + str(count) + '-' + match + '\n'

    embed.add_field(name='Dates', value=dates, inline=False)
    await ctx.send(embed=embed)


@bot.slash_command(name='history')
async def history(ctx, draft: int = None):
    hist = read_history(ctx)
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
    embed.add_field(name=f'Less winners: {
                    totalB}', value=playersB, inline=False)
    embed.add_field(name='Matches: ' + str(totalA + totalB),
                    value=marchlist, inline=False)
    await ctx.send(embed=embed)


@ bot.command(name='event')
async def event(ctx, action='', date=None):
    data = None
    ifclose = False
    match action.lower():
        case 'start':
            data = await start(ctx, date)
            await print_event(ctx, data)
        case 'close':
            if ctx.author.id == EU:
                ifclose = await close(ctx)
                if ifclose:
                    await history(ctx)
                else:
                    await print_event(ctx, data)
            else:
                await print_event(ctx, data)
        case 'clear':
            if ctx.author.id == EU:
                await clear()
            await print_event(ctx, data)
        case 'rdm':
            data = event_rdm(ctx)
            await print_event(ctx, data)
        case _:
            await print_event(ctx, data)


def event_rdm(ctx):
    df = read_players(ctx)
    half_size = len(df) // 2
    random_indices = numpy.random.choice(df.index, half_size, replace=False)
    df.loc[random_indices, 'Team'] = 'A'
    df.loc[~df.index.isin(random_indices), 'Team'] = 'B'
    df.to_csv(filenames(ctx, FILE_PLAYERS), sep=',',
              index=False, encoding='utf-8')
    return df


async def clear(ctx):
    dataframe_players().to_csv(filenames(ctx, FILE_PLAYERS),
                               sep=',', index=False, encoding='utf-8')
    dataframe_current().to_csv(filenames(ctx, FILE_CURRENT),
                               sep=',', index=False, encoding='utf-8')
    read_start(ctx, True)


async def start(ctx, date):
    read_start(ctx, True, date)
    df = read_players(ctx)
    counts = df['Team'].value_counts()
    if len(df) in [4, 6, 8] and counts.nunique() == 1 and len(counts) == 2:
        TeamA = df[df['Team'] == 'A']
        TeamB = df.drop(TeamA.index)
        Mlist = itertools.product(
            TeamA['Player'].tolist(), TeamB['Player'].tolist())
        df = pandas.DataFrame(Mlist, columns=['Team A', 'Team B'])
        df.insert(1, 'W-A', '-')
        df.insert(3, 'W-B', '-')
        df.to_csv(filenames(ctx, FILE_CURRENT), sep=',',
                  index=False, encoding='utf-8')
    return df


def read_start(ctx, clean=False, datein=None):
    draftID = ''
    if not clean:
        with open(FILE_START, 'r') as f:
            draftID = f.readline()
        f.close()
    if len(draftID) == 0 or clean:
        if datein is None:
            draftID = date.today().strftime("%d/%m/%Y")
            draftID = draftID + '-' + datetime.now().strftime("%H%M%S")
        else:
            draftID = datein + '-' + datetime.now().strftime("%H%M%S")
        with open(filenames(ctx, FILE_START), 'w') as f:
            f.write(draftID)
        f.close()
    return draftID


async def close(ctx):
    current = read_current(ctx)
    current = current[(current['W-A'] != '-') & (current['W-B'] != '-')]
    windiff_teamA = windiff_a(current)
    fechou = False
    if windiff_teamA != 0:
        fechou = True
        history = read_history(ctx)
        draftID = read_start(ctx)
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
        history.to_csv(filenames(ctx, FILE_HISTORY), sep=',',
                       index=False, encoding='utf-8')
        await send_file(ctx)
        await clear(ctx)
    return fechou


@bot.slash_command(name='score')
async def score(ctx):
    dataFrame = read_history(ctx)
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

    embed = discord.Embed(title=f"__**Scoreboard:**__", color=0x03f8fc)
    pos = 0
    list = dt.values.tolist()
    for match in list:
        pos = pos + 1
        embed.add_field(name=f'Rank: {pos}',
                        value=f'Player: {match[4]}\nDraft: {match[0]}/{match[1]} - {match[0]*100//match[1]}%\nMatch: {match[2]}/{match[3]} - {match[2]*100//match[3]}%', inline=True)
    await ctx.send(embed=embed)


@ bot.command(name='breakatie')
async def breakatie(ctx, user1, user2):
    event_playes = read_current(ctx)
    windiff_teamA = windiff_a(event_playes)
    if windiff_teamA == 0:
        objs = event_playes.loc[event_playes['Team A'].isin(
            [user1, user2]) & event_playes['Team B'].isin([user1, user2])]
        if len(objs) == 1:
            objs.at[objs.index[0], 'W-A'] = '-'
            objs.at[objs.index[0], 'W-B'] = '-'
            event_playes = pandas.concat(
                [event_playes, objs], ignore_index=True)
            event_playes.to_csv(filenames(ctx, FILE_CURRENT), sep=',',
                                index=False, encoding='utf-8')
    await print_event(ctx)


@ bot.command(name='play')
async def play(ctx, team=None):
    event_playes = read_players(ctx)
    event_playes = add_player(event_playes, id_to_usr(ctx.author.id), team)
    event_playes.to_csv(filenames(ctx, FILE_PLAYERS),
                        sep=',', index=False, encoding='utf-8')
    await print_event(ctx)


@ bot.command(name='playersB')
async def playersB(ctx, p1, p2=None, p3=None, p4=None):
    await add_players(ctx, 'B', p1, p2, p3, p4)


@ bot.command(name='playersA')
async def playersA(ctx, p1, p2=None, p3=None, p4=None):
    await add_players(ctx, 'A', p1, p2, p3, p4)


@ bot.command(name='players')
async def players(ctx, p1, p2=None, p3=None, p4=None):
    await add_players(ctx, None, p1, p2, p3, p4)


async def add_players(ctx, team, p1, p2=None, p3=None, p4=None):
    event_playes = read_players(ctx)
    event_playes = add_player(event_playes, p1, team)
    event_playes = add_player(event_playes, p2, team)
    event_playes = add_player(event_playes, p3, team)
    event_playes = add_player(event_playes, p4, team)
    event_playes.to_csv(filenames(ctx, FILE_PLAYERS),
                        sep=',', index=False, encoding='utf-8')
    await print_event(ctx, event_playes)


def add_player(event_playes, user, team=None):
    if user is not None and len(event_playes) < 8:
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
        df2 = dataframe_players([[user, team]])
        event_playes = pandas.concat([event_playes, df2], ignore_index=True)
    return event_playes


def read_players(ctx):
    if os.stat(filenames(ctx, FILE_PLAYERS)).st_size == 0:
        return dataframe_players()
    else:
        return pandas.read_csv(filenames(ctx, FILE_PLAYERS))


def read_current(ctx):
    if os.stat(filenames(ctx, FILE_CURRENT)).st_size == 0:
        return dataframe_current()
    else:
        return pandas.read_csv(filenames(ctx, FILE_CURRENT))


def dataframe_current():
    return pandas.DataFrame(columns=['Team A', 'W-A', 'Team B', 'W-B'])


def dataframe_players(list=None):
    if list is None:
        return pandas.DataFrame(columns=['Player', 'Team'])
    else:
        return pandas.DataFrame(list, columns=['Player', 'Team'])


def read_history(ctx):
    if os.stat(filenames(ctx, FILE_HISTORY)).st_size == 0:
        return pandas.DataFrame(columns=['Date', 'Victory', 'Player', 'Match',
                                         'Game-Win', 'Opponent', 'Game-Lose'])
    else:
        return pandas.read_csv(filenames(ctx, FILE_HISTORY))


async def send_file(ctx):
    file_path = filenames(ctx, FILE_HISTORY)
    try:
        target_channel = discord.utils.get(
            ctx.guild.channels, name='db')
        with open(file_path, 'rb') as file:
            file_data = discord.File(file)
            await target_channel.send(file=file_data)
    except Exception:
        return


@ bot.event
async def on_ready():
    await bot.change_presence()
    print('Running: {0.user}'.format(bot))


bot.run(my_secret)
