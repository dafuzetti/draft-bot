from discord.ext import commands
from discord import app_commands
import discord
import itertools
import pandas
import numpy
import os
from datetime import datetime
from datetime import date
import table2ascii
from table2ascii import Alignment, PresetStyle

my_secret = os.environ['TOKEN']
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
FILE_CURRENT = 'current.csv'
FILE_HISTORY = 'history.csv'
FILE_START = 'start.txt'
EU = 723638398312513586


def draftid():
    str = date.today().strftime("%d/%m/%Y")
    str = str + '-' + datetime.now().strftime("%H%M%S")
    return str


def windiff_a(current):
    diff = (current[current['W-A'] == 2]['Team A'].count()) - \
        (current[current['W-B'] == 2]['Team B'].count())

    diff2 = (current[current['W-A'] == 1]['Team A'].count()) - \
        (current[current['W-B'] == 1]['Team B'].count())

    return diff + (diff2/10)


async def print_event(ctx, print=None):
    dt = print
    list = []
    if dt is None:
        dt = read_current()
    list = dt.values.tolist()
    name = await read_start()
    embed = discord.Embed(title=f"__**{name}:**__",
                          color=0x03f8fc, timestamp=ctx.message.created_at)
    for match in list:
        embed.add_field(name=f'{match[4]}',
                        value=f'Draft win: {match[0]}\nDraft played: {match[1]}\nMatch win: {match[2]}\nMatch played: {match[3]}', inline=False)
    await ctx.send(embed=embed)


async def print_eventORIGINAL(ctx, print=None):
    dt = print
    if dt is None:
        dt = read_current()
    output = table2ascii.table2ascii(
        header=list(dt.columns.values),
        body=dt.values.tolist(),
        style=PresetStyle.thin_compact
    )
    await ctx.send(output)


def id_to_usr(id):
    return '<@'+str(id)+'>'


async def resultado(ctx, userW, userL, loss=0):
    gameloss = 0
    if loss != 0:
        gameloss = 1
    df = read_current()
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
        df.to_csv(FILE_CURRENT, sep=',', index=False, encoding='utf-8')
    await print_event(ctx, df)


@bot.command(name='lose')
async def lose(ctx, player_win, gameloss=0):
    await resultado(ctx, player_win, id_to_usr(ctx.author.id), gameloss)


@bot.command(name='win')
async def win(ctx, player_lost, gameloss=0):
    await resultado(ctx, id_to_usr(ctx.author.id), player_lost, gameloss)


@ bot.command(name='result')
async def result(ctx, player_win, player_lose, gameloss=0):
    await resultado(ctx, player_win, player_lose, gameloss)


@bot.command(name='event')
async def event(ctx, action=''):
    df = read_current()
    match action.lower():
        case 'start':
            if len(df) in [4, 6, 8]:
                df = await start(ctx, df)
        case 'close':
            if ctx.author.id == EU:
                df = await close(ctx, df)
        case 'clear':
            if ctx.author.id == EU:
                df = await clear()

    await print_event(ctx, df)


async def clear():
    df = dataframe_current_players()
    df.to_csv(FILE_CURRENT, sep=',', index=False, encoding='utf-8')
    return df


async def start(ctx, dfcurrent):
    with open(FILE_START, 'w') as f:
        f.write(draftid())
    f.close()
    df = dfcurrent
    TeamA = df.head(len(df) // 2)
    TeamB = df.drop(TeamA.index)
    Mlist = itertools.product(
        TeamA['Player'].tolist(), TeamB['Player'].tolist())
    df = pandas.DataFrame(Mlist, columns=['Team A', 'Team B'])
    df.insert(1, 'W-A', '-')
    df.insert(3, 'W-B', '-')
    df.to_csv(FILE_CURRENT, sep=',', index=False, encoding='utf-8')
    return df


async def read_start():
    with open(FILE_START, 'r') as f:
        draftID = f.readline()
    f.close()
    if len(draftID) == 0:
        draftID = draftid()
    return draftID


async def close(ctx, dfcurrent):
    current = dfcurrent
    windiff_teamA = windiff_a(current)
    if windiff_teamA != 0:
        history = read_history()
        draftID = read_start()
        teamA = current
        teamB = current
        teamA = teamA.rename(
            columns={"Team A": "Player", "Team B": "Opponent",
                     "W-B": "Game-Loss"})
        teamA['Match'] = numpy.where(teamA['W-A'] != 2, 0, 1)
        teamA.drop('W-A', axis=1, inplace=True)
        teamB = teamB.rename(
            columns={"Team B": "Player", "Team A": "Opponent",
                     "W-A": "Game-Loss"})
        teamB['Match'] = numpy.where(teamB['W-B'] != 2, 0, 1)
        teamB.drop('W-B', axis=1, inplace=True)
        if (windiff_teamA > 0):
            teamA.insert(0, 'Victory', 1)
            teamB.insert(0, 'Victory', 0)
        else:
            teamA.insert(0, 'Victory', 0)
            teamB.insert(0, 'Victory', 1)
        current = pandas.concat([teamA, teamB], ignore_index=True)
        current.insert(0, 'Date', draftID)
        current = current.reindex(
            columns=['Date', 'Victory', 'Player', 'Match',
                     'Opponent', 'Game-Loss'])
        current.sort_values(['Victory', 'Player', 'Match', 'Game-Loss'],
                            axis=0, inplace=True, ascending=False,
                            na_position='first')
        history = pandas.concat([history, current], ignore_index=True)
        history.to_csv(FILE_HISTORY, sep=',',
                       index=False, encoding='utf-8')
        current.drop('Date', axis=1, inplace=True)
        await clear()
    return current


@bot.command(name='score')
async def score(ctx):
    dataFrame = read_history()
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
    await print_event(ctx, dt.head(10))


@ bot.command(name='breakatie')
async def breakatie(ctx, user1, user2):
    event_playes = read_current()
    windiff_teamA = windiff_a(event_playes)
    print(windiff_teamA)
    if windiff_teamA == 0:
        objs = event_playes.loc[event_playes['Team A'].isin(
            [user1, user2]) & event_playes['Team B'].isin([user1, user2])]
        if len(objs) == 1:
            objs.at[objs.index[0], 'W-A'] = '-'
            objs.at[objs.index[0], 'W-B'] = '-'
            event_playes = pandas.concat(
                [event_playes, objs], ignore_index=True)
            event_playes.to_csv(FILE_CURRENT, sep=',',
                                index=False, encoding='utf-8')
    await print_event(ctx, event_playes)


@ bot.command(name='play')
async def play(ctx, u1=None, u2=None, u3=None,
               u4=None, u5=None, u6=None, u7=None):
    event_playes = read_current()
    event_playes = add_player(event_playes, id_to_usr(ctx.author.id))
    event_playes = add_player(event_playes, u1)
    event_playes = add_player(event_playes, u2)
    event_playes = add_player(event_playes, u3)
    event_playes = add_player(event_playes, u4)
    event_playes = add_player(event_playes, u5)
    event_playes = add_player(event_playes, u6)
    event_playes = add_player(event_playes, u7)
    event_playes.sort_values(['Player'], axis=0,
                             inplace=True, na_position='first')
    event_playes.to_csv(FILE_CURRENT, sep=',', index=False, encoding='utf-8')
    await print_event(ctx, event_playes)


def add_player(event_playes, user):
    if user is not None and user not in event_playes.values:
        df2 = dataframe_current_players([user])
        event_playes = pandas.concat([event_playes, df2], ignore_index=True)
    return event_playes


def read_current():
    if os.stat(FILE_CURRENT).st_size == 0:
        return dataframe_current_players()
    else:
        return pandas.read_csv(FILE_CURRENT)


def dataframe_current_players(list=None):
    if list is None:
        return pandas.DataFrame(columns=['Player'])
    else:
        return pandas.DataFrame(list, columns=['Player'])


def read_history():
    if os.stat(FILE_HISTORY).st_size == 0:
        return pandas.DataFrame(columns=['Date', 'Victory', 'Player', 'Match',
                                'Opponent', 'Game-Loss'])
    else:
        return pandas.read_csv(FILE_HISTORY)


@ bot.event
async def on_ready():
    await bot.change_presence()
    print('Running: {0.user}'.format(bot))


bot.run(my_secret)
