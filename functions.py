import discord
import itertools
import numpy
import math
import data_base


def add_players(ctx, team, p1: discord.User, p2: discord.User = None,
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
    for player in list:
        if player is not None:
            data_base.new_player(ctx, player.mention, team)


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
    if len(df) in [4, 6, 8] and counts.nunique() == 1 and len(counts) == 2:
        TeamA = df[df['team'] == 1]
        TeamB = df.drop(TeamA.index)
        Mlist = itertools.product(
            TeamA['player'].tolist(), TeamB['player'].tolist())
        data_base.save_matches(ctx, Mlist)
    return


def print_event(ctx, event=None):
    embed = discord.Embed(title="__**No event**__", color=0x03f8fc)
    event_id = event
    if (event_id is None):
        event_id = data_base.find_event(ctx)
    if event_id is not None:
        matches = data_base.read_matches(ctx, event_id)
        if len(matches) > 0:
            embed = print_event_started(ctx, matches)
        else:
            players = data_base.read_players(ctx, event_id)
            embed = print_players(ctx, players)
    return embed


def print_players(ctx, players):
    dt = players
    embed = discord.Embed(title="__**Players**__", color=0x03f8fc)
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


def print_event_started(ctx, dt):
    name = "Evento"
    list = dt.values.tolist()
    embed = discord.Embed(title=f"__**{name[:10]}**__", color=0x03f8fc)
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
        if match[1] == match[3] and match[3] == 0:
            matches = matches + str(match[0]) + \
                ' - ' + str(match[2]) + '\n'
        else:
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
    return embed


def resultado(ctx, player_w, player_l, losses):
    data_base.update_matches(ctx, player_w, player_l, losses)
