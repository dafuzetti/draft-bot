import pandas
import os
import psycopg2
import discord
from urllib.parse import urlparse
from datetime import date
from decouple import config

SQL_INSERT_EVENT = """INSERT INTO event(guild, channel, date, teams, type, owner)
            VALUES(%s, %s, %s, %s, %s, %s) RETURNING id;"""
SQL_UPDATE_EVENT = """UPDATE event SET victory = %s WHERE id = %s;"""
SQL_INSERT_TEAMS = """INSERT INTO teams(event, player, team)
            VALUES(%s, %s, %s);"""
SQL_DELETE_TEAMS = """DELETE FROM teams WHERE event = '%s';"""
SQL_INSERT_MATCH = """INSERT INTO match(event, player, opponent)
            VALUES(%s, %s, %s);"""
SQL_UPDATE_MATCH = """UPDATE match SET win = %s, lose = %s 
            WHERE event = %s AND player = %s AND opponent = %s;"""
FILE_HISTORY = 'history.csv'
env = config("ENV")
db_key = config("DB_KEY")


def get_conn():
    database_url = 'postgres://postgres:' + db_key + \
        '@roundhouse.proxy.rlwy.net:13681/railway'
    if env == "TES":
        database_url = 'postgres://postgres:' + db_key + \
            '@roundhouse.proxy.rlwy.net:13681/railway'
    elif env == "PRO":
        database_url = 'postgres://postgres:' + db_key + \
            '@viaduct.proxy.rlwy.net:29301/railway'
    url = urlparse(database_url)
    connection = psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )
    return connection


async def send_file(ctx):
    file_path = filenames(ctx, FILE_HISTORY)
    target_channel = discord.utils.get(
        ctx.guild.channels, name='db')
    with open(file_path, 'rb') as file:
        file_data = discord.File(file)
        await target_channel.send(file=file_data)


async def save_history(ctx, dt):
    dt.to_csv(filenames(ctx, FILE_HISTORY), sep=',',
              index=False, encoding='utf-8')


def filenames(ctx, name):
    folder_path = 'channel_' + str(ctx.guild.id)
    full_path = os.path.join(folder_path, name)
    return str(full_path)


def find_event(ctx):
    event_id = None
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM event WHERE guild = '%s' AND channel = '%s' AND victory IS NULL",
                    (ctx.guild_id, ctx.channel_id,))
        rows = cur.fetchone()
        if rows is not None:
            if len(rows) == 0:
                cur.execute("SELECT * FROM event WHERE guild = '%s' AND victory IS NULL",
                            (ctx.guild_id, ctx.channel_id,))
                rows = cur.fetchone()
            if len(rows) > 0:
                event_id = rows[0]
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return event_id


def new_player(ctx, mention, to_team: int):
    conn = None
    event_id = find_event(ctx)
    if event_id is not None:
        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute(SQL_INSERT_TEAMS, (event_id, mention, to_team,))
            conn.commit()
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()


def clear_event(ctx):
    conn = None
    event_id = find_event(ctx)
    if event_id is not None:
        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute(SQL_DELETE_TEAMS, (event_id,))
            conn.commit()
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()


def update_matches(ctx, player_w, player_l, lose):
    conn = None
    event_id = find_event(ctx)
    try:
        conn = get_conn()
        cur = conn.cursor()
        updates = cur.execute(
            SQL_UPDATE_MATCH, (2, lose, event_id, player_w, player_l,))
        if updates is None:
            cur.execute(SQL_UPDATE_MATCH,
                        (lose, 2, event_id, player_l, player_w,))
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


def save_matches(ctx, list):
    conn = None
    event_id = find_event(ctx)
    try:
        conn = get_conn()
        cur = conn.cursor()
        for match in list:
            cur.execute(SQL_INSERT_MATCH, (event_id, match[0], match[1],))
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


def new_event(ctx, teams: int, type: int):
    conn = None
    event_id = None
    event_date = date.today().strftime("%Y%m%d")
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM event WHERE guild = '%s' AND channel = '%s' AND victory IS NULL",
                    (ctx.guild_id, ctx.channel_id,))
        rows = cur.fetchall()
        if len(rows) == 0:
            cur.execute(SQL_INSERT_EVENT, (ctx.guild_id, ctx.channel_id,
                        event_date, teams, type, ctx.user.mention,))
            event_id = cur.fetchone()[0]
            cur.execute(SQL_INSERT_TEAMS, (event_id, ctx.user.mention, 1,))
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


def close_event(ctx, event=None):
    event_id = event
    if event_id is None:
        event_id = find_event(ctx)
    conn = None
    if event_id is not None:
        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute(
                """SELECT
                        EVENT,
                        TEAM,
                        COALESCE(SUM(1) filter (where WIN = 2), 0) as WIN,
                        COALESCE(SUM(1) filter (where LOSE = 1), 0) as LOS
                    FROM(
                        SELECT
                            M.ID,
                            M.EVENT,
                            M.PLAYER PLAYER,
                            T1.TEAM TEAM,
                            M.WIN,
                            M.LOSE
                        FROM
                            match as M,
                            TEAMS AS T1,
                            TEAMS AS T2
                        WHERE
                            M.EVENT = T1.EVENT
                        AND M.EVENT = T2.EVENT
                        AND M.EVENT = %s
                        AND T1.PLAYER = M.PLAYER
                        AND T2.PLAYER = M.OPPONENT
                        union
                        SELECT
                            M.ID,
                            M.EVENT,
                            M.OPPONENT PLAYER,
                            T2.TEAM TEAM,
                            M.LOSE,
                            M.WIN
                        FROM
                            match as M,
                            TEAMS AS T1,
                            TEAMS AS T2
                        WHERE
                            M.EVENT = T1.EVENT
                        AND M.EVENT = T2.EVENT
                        AND M.EVENT = %s
                        AND T1.PLAYER = M.PLAYER
                        AND T2.PLAYER = M.OPPONENT
                    ) GROUP BY EVENT, TEAM
                    ORDER BY WIN desc, LOS;""", (event_id, event_id,))
            row = cur.fetchone()
            if row is not None:
                cur.execute(SQL_UPDATE_EVENT, (row[1], row[0],))
            conn.commit()
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()
    return event_id


def read_players(ctx, event=None):
    event_id = event
    if event_id is None:
        event_id = find_event(ctx)
    conn = None
    rows = None
    if event_id is not None:
        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute(
                "SELECT player, team FROM teams WHERE event=%s ORDER BY team, player", (event_id,))
            rows = cur.fetchall()
            conn.commit()
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()
    return dataframe_players(rows)


def read_matches(ctx, event=None):
    event_id = event
    if event_id is None:
        event_id = find_event(ctx)
    conn = None
    rows = None
    if event_id is not None:
        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute(
                "SELECT player, COALESCE(win, 0), opponent, COALESCE(lose, 0) FROM match WHERE event=%s ORDER BY player, opponent", (event_id,))
            rows = cur.fetchall()
            conn.commit()
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()
    return dataframe_current(rows)


def dataframe_current(list=None):
    if list is None:
        return pandas.DataFrame(columns=['Team A', 'W-A', 'Team B', 'W-B'])
    else:
        return pandas.DataFrame(list, columns=['Team A', 'W-A', 'Team B', 'W-B'])


def dataframe_players(list=None):
    if list is None:
        return pandas.DataFrame(columns=['player', 'team'])
    else:
        return pandas.DataFrame(list, columns=['player', 'team'])


def read_history(ctx):
    if os.stat(filenames(ctx, FILE_HISTORY)).st_size == 0:
        return pandas.DataFrame(columns=['Date', 'Victory', 'Player', 'Match',
                                         'Game-Win', 'Opponent', 'Game-Lose'])
    else:
        return pandas.read_csv(filenames(ctx, FILE_HISTORY))
