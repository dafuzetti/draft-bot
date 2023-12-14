import pandas
import os
from datetime import datetime
from datetime import date

FILE_CURRENT = 'current.csv'
FILE_HISTORY = 'history.csv'
FILE_PLAYERS = 'players.csv'
FILE_START = 'start.txt'


async def folder(guild):
    folder_path = 'channel_' + str(guild.id)
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


async def save_history(ctx, dt):
    dt.to_csv(filenames(ctx, FILE_HISTORY), sep=',',
              index=False, encoding='utf-8')


async def save_current(ctx, dt):
    dt.to_csv(filenames(ctx, FILE_CURRENT), sep=',',
              index=False, encoding='utf-8')


async def save_players(ctx, dt):
    dt.to_csv(filenames(ctx, FILE_PLAYERS), sep=',',
              index=False, encoding='utf-8')


def filenames(ctx, name):
    folder_path = 'channel_' + str(ctx.guild.id)
    full_path = os.path.join(folder_path, name)
    return str(full_path)


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


def read_start(ctx, datein=None):
    draftID = ''
    if datein is None:
        datein = date.today().strftime("%d/%m/%Y")
        with open(filenames(ctx, FILE_START), 'r') as f:
            draftID = f.readline()
        f.close()
    if len(draftID) == 0:
        draftID = str(datein) + '-' + datetime.now().strftime("%H%M%S")
        with open(filenames(ctx, FILE_START), 'w') as f:
            f.write(draftID)
        f.close()
    return draftID