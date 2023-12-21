import discord
import itertools
import numpy
import math
import data_base


def add_players(ctx, same_team, p1: discord.User, p2: discord.User = None,
                p3: discord.User = None, p4: discord.User = None,
                p5: discord.User = None, p6: discord.User = None,
                p7: discord.User = None, p8: discord.User = None):
    list = []
    list.append(p1)
    list.append(p2)
    list.append(p3)
    list.append(p4)
    list.append(p5)
    list.append(p6)
    list.append(p7)
    list.append(p8)
    data_base.new_player(ctx, list, same_team)


def resultado(ctx, player_w, player_l, losses):
    data_base.update_matches(ctx, player_w, player_l, losses)


def event_rdm(ctx):
    df = data_base.read_players(ctx)
    half_size = len(df) // 2
    random_indices = numpy.random.choice(df.index, half_size, replace=False)
    df.loc[random_indices, 'Team'] = 'A'
    df.loc[~df.index.isin(random_indices), 'Team'] = 'B'
    data_base.save_players(ctx, df)
    return df


def start(ctx):
    df = data_base.read_players(ctx)
    counts = df['team'].value_counts()
    if len(df) % 2 == 0 and counts.nunique() == 1 and len(counts) == 2:
        TeamA = df[df['team'] == 1]
        TeamB = df.drop(TeamA.index)
        Mlist = itertools.product(
            TeamA['player'].tolist(), TeamB['player'].tolist())
        data_base.save_matches(ctx, Mlist)
    return


def print_history(ctx, channel: bool = False):
    hist = data_base.read_events(ctx, channel)
    embed = discord.Embed(title="__**Events**__", color=0x03f8fc)
    count = 0
    dates = ''
    active = ''
    for draft in hist:
        count = count + 1
        if draft[5] is not None:
            dates = dates + str(count) + ' - ' + str(
                draft[2])[6:] + '/' + str(draft[2])[4:~1] + '/' + str(
                draft[2])[0:~3] + ' (' + str(draft[7]) + ') ' + draft[6] + ' ID: ' + str(
                draft[0]) + '\n'
        else:
            active = active + str(count) + ' - ' + str(
                draft[2])[6:] + '/' + str(draft[2])[4:~1] + '/' + str(
                draft[2])[0:~3] + ' (' + str(draft[7]) + ') ' + draft[6] + ' ID: ' + str(
                draft[0]) + '\n'
    embed.add_field(name='History', value=dates, inline=False)
    embed.add_field(name='Active', value=active, inline=False)
    return embed


def print_event(ctx, event=None):
    embed = discord.Embed(title="__**No event**__", color=0x03f8fc)
    event_id = event
    if (event_id is None):
        event_id = data_base.find_event(ctx)
    if event_id is not None:
        matches = data_base.read_matches(ctx, event_id)
        event_data = data_base.read_event(ctx, event_id)
        if len(matches) > 0:
            embed = print_event_started(ctx, matches, event_data)
        else:
            players = data_base.read_players(ctx, event_id)
            embed = print_players(ctx, players, event_data)
    return embed


def print_players(ctx, players, event_obj):
    dt = players
    embed = discord.Embed(
        title="__**Event channel:**__ " + event_obj[1] + '\n__**Players:**__', color=0x03f8fc)
    list = dt.values.tolist()
    playersA = ''
    playersB = ''
    for match in list:
        if str(match[1]) == "1":
            playersA = playersA + str(match[0]) + ' '
        if str(match[1]) == "2":
            playersB = playersB + str(match[0]) + ' '
    embed.add_field(name='Team A', value=playersA, inline=False)
    embed.add_field(name='Team B', value=playersB, inline=False)
    return embed


def print_event_started(ctx, dt, event_obj):
    list = dt.values.tolist()
    embed = discord.Embed(
        title="__**Event channel:**__ " + event_obj[1], color=0x03f8fc)
    count = len(list)
    matches = ''
    playersA = ''
    playersB = ''
    pos = 0
    winA = 0
    winB = 0
    nrp = math.sqrt(count)
    toadd = 1

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
        if match[1] == match[3] and match[3] == 0:
            matches = matches + str(match[0]) + \
                ' - ' + str(match[2]) + '\n'
        else:
            matches = matches + str(match[0]) + ' ' + str(match[1]) + \
                '-' + str(match[3]) + ' ' + str(match[2]) + '\n'

    emjA = ''
    emjB = ''
    if str(event_obj[4]) == '2':
        emjA = ':skull:'
        emjB = ':trophy:'
    elif str(event_obj[4]) == '1':
        emjA = ':trophy:'
        emjB = ':skull:'
    elif str(event_obj[4]) == '0':
        emjA = '🍕'
        emjB = '🍕'

    embed.add_field(name='Team A ' + str(emjA),
                    value=f'Players: {playersA}\nWin: {winA}', inline=False)
    embed.add_field(name='Team B ' + str(emjB),
                    value=f'Players: {playersB}\nWin: {winB}', inline=False)
    embed.add_field(name=f'Pairings: {winA + winB}/{count}',
                    value=matches, inline=False)
    return embed
