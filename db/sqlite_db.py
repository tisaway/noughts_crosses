import sqlite3 as sq
from create_bot import bot 

#Подключается к БД и создает таблицы, если их нет
def sql_start():
    global conn, cur 
    conn = sq.connect('noughts_crosses.db')
    cur = conn.cursor()
    if conn:
        print('Connected to db!')
    conn.execute('CREATE TABLE IF NOT EXISTS score(player_id TEXT PRIMARY KEY, wins INT, losses INT, draws INT)')
    #msg_id - сообщение, в котором будет выводиться игровое поле, turn (true - может ходить), символ - чем отмечен в поле игрок (1 или 2)
    conn.execute('CREATE TABLE IF NOT EXISTS players(player_id TEXT PRIMARY KEY, msg_id TEXT, game_id INTEGER, turn BOOLEAN, symbol INT)')
    #grid - игровое поле в формате "000000000"
    conn.execute('CREATE TABLE IF NOT EXISTS games(game_id INTEGER PRIMARY KEY AUTOINCREMENT, grid TEXT)')
    #Таблица ожидания противника была создана для быстрого поиска
    conn.execute('CREATE TABLE IF NOT EXISTS waiting_list(player_id TEXT PRIMARY KEY)')
    conn.commit()

#Принимает на вход id пользователя и добавляет его в список ожидания
async def sql_waiting_list_add(player_id):
    cur.execute('INSERT or IGNORE INTO waiting_list VALUES (?)', (player_id, ))
    conn.commit()

#Удаляет из списка ожидания по id пользователя
async def sql_waiting_list_delete(player_id):
    cur.execute('DELETE FROM waiting_list WHERE player_id == ?', (player_id,))
    conn.commit()

#Возвращает id первого пользователя в списке ожидания, чтобы с ним сыграть (Int либо None)
async def sql_waiting_list_get_rival():
    rival_id = cur.execute('SELECT player_id FROM waiting_list').fetchone()
    if rival_id:
        return rival_id[0]
    return rival_id

async def sql_waiting_list_read():
    return cur.execute('SELECT * FROM waiting_list').fetchall()


#Добавляет пользователя в таблицу со счетом по id и выставляет начальные значения
async def sql_score_add(player_id):
    cur.execute('INSERT or IGNORE INTO score VALUES (?, 0, 0, 0)', (player_id, ))
    conn.commit()

#Прибавляет значения к счету игрока
async def sql_score_increase(player_id, wins = 0, losses = 0, draws = 0):
    score = await sql_score_get(player_id)
    cur.execute('UPDATE score SET wins = ?, losses = ?, draws = ? WHERE player_id == ?', (score[0]+wins, score[1]+losses, score[2]+draws, player_id))

#Возвращает кортеж со счетом пользователя по порядку (wins, losses, draws)
#Если нет записи, то добавляет новую обнуленную
async def sql_score_get(player_id):
    score = cur.execute('SELECT wins, losses, draws FROM score WHERE player_id == ?', (player_id, )).fetchone()
    if not score:
        await sql_score_add(player_id)
        score = cur.execute('SELECT wins, losses, draws FROM score WHERE player_id == ?', (player_id, )).fetchone()
    return score

async def sql_score_read():
    return cur.execute('SELECT * FROM score').fetchall()


#Создает обнуленное игровое поле и возвращает его id (int либо None)
async def sql_games_create():
    cur.execute('INSERT or IGNORE INTO games (grid) VALUES ("000000000")')
    game_id = cur.execute('SELECT last_insert_rowid()').fetchone()
    conn.commit()
    if game_id:
        return game_id[0]
    return game_id

#Удаляет запись поля по id игры
async def sql_game_delete(game_id):
    cur.execute('DELETE FROM games WHERE game_id == ?', (game_id,))
    conn.commit()

#Меняет значение игрового поля на новое (grid) в записи под game_id
async def sql_games_update_grid(game_id, grid):
    return cur.execute('UPDATE games SET grid = ? WHERE game_id == ?', (grid, game_id))
    conn.commit()

#Возвращает игровое поле по game_id в формате строки (либо None)
async def sql_games_get_grid(game_id):
    grid = cur.execute('SELECT grid FROM games WHERE game_id == ?', (game_id, )).fetchone()
    if grid:
        return grid[0]
    return grid

async def sql_games_read():
    return cur.execute('SELECT * FROM games').fetchall()


#Вносит id пользователя и id сообщения, в котором в будущем будет игровое поле
async def sql_players_add(player_id, msg_id):
    cur.execute('INSERT or REPLACE INTO players (player_id, msg_id) VALUES (?, ?)', (player_id, msg_id))
    conn.commit()

#Вносит в уже существующую запись данные о самой игре - id игры, turn - ход ли игрока сейчас
#Прибвляет к turn 1, чтобы получить не ноль(т.к. 0 - пустая клетка)
async def sql_players_update_game(player_id, game_id, turn):
    cur.execute('UPDATE players SET game_id = ?, turn = ?, symbol = ? WHERE player_id == ?', (game_id, turn, turn+1, player_id))
    conn.commit()

#Меняет ход игрока на новый
async def sql_players_update_turn(player_id, turn):
    cur.execute('UPDATE players SET turn = ? WHERE player_id == ?', (turn, player_id))
    conn.commit()

#Возвращает id противника (int либо None) в УЖЕ существующей игре
async def sql_players_get_rival(player_id, game_id):
    rival_id = cur.execute('SELECT player_id FROM players WHERE game_id == ? AND player_id != ?', (game_id, player_id)).fetchone()
    if rival_id:
        return rival_id[0]
    return rival_id

#Возвращает id сообщения с игровым полем (int либо None)
async def sql_players_get_msg_id(player_id):
    msg_id = cur.execute('SELECT msg_id FROM players WHERE player_id == ?', (player_id,)).fetchone()
    if msg_id:
        return msg_id[0]
    return msg_id

#Возвращает id текущей игры пользователя с player_id (int либо None)
async def sql_players_get_game_id(player_id):
    game_id = cur.execute('SELECT game_id FROM players WHERE player_id == ?', (player_id,)).fetchone()
    if game_id:
        return game_id[0]
    return game_id

#Возвращает значение, означающие ход ли сейчас игрока (bool либо None)
async def sql_players_get_turn(player_id):
    turn = cur.execute('SELECT turn FROM players WHERE player_id == ?', (player_id, )).fetchone()
    if turn:
        return turn[0]
    return turn

#Возвращает символ игрока по его id (int либо None)
async def sql_players_get_symbol(player_id):
    symbol = cur.execute('SELECT symbol FROM players WHERE player_id == ?', (player_id, )).fetchone()
    if symbol:
        return symbol[0]
    return symbol

#Ищет победителя по символу и возвращает его id (int либо None)
async def sql_players_get_winner(game_id, symbol):
    winner_id = cur.execute('SELECT player_id FROM players WHERE game_id == ? AND symbol == ?', (game_id, symbol)).fetchone()
    if winner_id:
        return winner_id[0]
    return winner_id

#Ищет проигравшего по символу ПОБЕДИТЕЛЯ и возвращает его id (int либо None)
async def sql_players_get_loser(game_id, winner_symbol):
    loser_id = cur.execute('SELECT player_id FROM players WHERE game_id == ? AND symbol != ?', (game_id, winner_symbol)).fetchone()
    if loser_id:
        return loser_id[0]
    return loser_id

async def sql_players_read():
    return cur.execute('SELECT * FROM players').fetchall()
