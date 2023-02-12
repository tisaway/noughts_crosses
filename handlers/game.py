from aiogram import types, Dispatcher
from random import randint

from create_bot import dp, bot
from db import sqlite_db
from keyboards import keyboard_searching, keyboard_menu, keyboard_get_qrid


#Создает игру в БД, добавляя ее id к записям игроков с id player_id_0 и player_id_1 соответсвенно
async def create_game(player_id_0, player_id_1):
    id_game = await sqlite_db.sql_games_create()

    turn = randint(0, 1)
    await sqlite_db.sql_players_update_game(player_id_0, id_game, turn)
    await sqlite_db.sql_players_update_game(player_id_1, id_game, not turn)

#Находит сообщение с игрой по id пользователя и обновляет его (с новым полем и текстом)
async def edit_grid_messege(player_id, text = 'Игра:'):
    message_id = await sqlite_db.sql_players_get_msg_id(player_id)
    grid = await sqlite_db.sql_games_get_grid(await sqlite_db.sql_players_get_game_id(player_id))
    keyboard = await keyboard_get_qrid(grid)
    await bot.edit_message_text(chat_id=player_id, message_id=message_id, text=text, reply_markup = keyboard)

#Редактирует сообщение с игрой игроков id player_id_0 и player_id_1 в зависимости от того, чей ход
async def resend_grid(player_id_0, player_id_1):
    text1 = 'ТВОЙ ХОД!'
    text2 = 'Сейчас ход противника.'
    if await sqlite_db.sql_players_get_turn(player_id_0):
        await edit_grid_messege(player_id_0, text1)
        await edit_grid_messege(player_id_1, text2)
    else:
        await edit_grid_messege(player_id_0, text2)
        await edit_grid_messege(player_id_1, text1)

#Создает игру и присылает игровое поле для игроков с id player_id_0 и player_id_1 соответсвенно
async def start_game(player_id_0, player_id_1):
    await create_game(player_id_0, player_id_1)
    await resend_grid(player_id_0, player_id_1)

#Запуск игры при нахождении противника либо добавление в лист ожидания
async def find_rival(player_id):
    msg = await bot.send_message(player_id, 'Ожидание соперника...', reply_markup=keyboard_searching)
    msg_id = msg.message_id
    #Добавляем игрока в список игроков, если его там нет
    await sqlite_db.sql_players_add(player_id, msg_id)
    rival_id = await sqlite_db.sql_waiting_list_get_rival()
    #Если противник нашелся - удаляем его из спика ожидания и начинаем игру. 
    #Если нет - список пуст. Добавляем в него пользователя
    if rival_id:
        await sqlite_db.sql_waiting_list_delete(rival_id)
        await start_game(player_id, rival_id)
    else:   
        await sqlite_db.sql_waiting_list_add(player_id)

#Находит и удаляет сообщение с игровым полем у пользователя по его id
async def delete_game_message(player_id):
    message_id = await sqlite_db.sql_players_get_msg_id(player_id)
    await bot.delete_message(player_id, message_id=message_id)

#Удаляет сообщение с игрой, приавляет счетчик игрока (победа) по его id
async def win(player_id):
    await sqlite_db.sql_score_increase(player_id=player_id, wins=1)
    await delete_game_message(player_id)

    await bot.send_message(player_id, 'Ты победил!!! Что теперь?', reply_markup=keyboard_menu) 

#Удаляет сообщение с игрой, приавляет счетчик игрока (проигрыш) по его id
async def lose(player_id):
    await sqlite_db.sql_score_increase(player_id=player_id, losses=1)
    await delete_game_message(player_id)

    await bot.send_message(player_id, 'Ты проиграл :с Что теперь?', reply_markup=keyboard_menu) 

#Удаляет сообщение с игрой, приавляет счетчик игрока (ничья) по его id
async def draw(player_id):
    await sqlite_db.sql_score_increase(player_id=player_id, draws=1)
    await delete_game_message(player_id)

    await bot.send_message(player_id, 'Ничья! Что теперь?', reply_markup=keyboard_menu) 
    
#Принимает id игроков (победивших и выигравших). Удаляет игру из БД
async def end_game(winner, loser, game_id, is_draw = False):
    if is_draw:
        await draw(winner)
        await draw(loser)
    else:
        await win(winner)
        await lose(loser)
    await sqlite_db.sql_game_delete(game_id)

async def replace_symbol(str, id, new_symbol):
    return str[:id] + new_symbol + str[id+1:]

#Ищет в поле выигрышные комбинации и возвращает символ, свормировавший их
#0 - игроки не сформировали выигрышных комбинаций, 1 и 2 - символы игроков
async def who_won(grid):
    combinations = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]]
    for combination in combinations:
        num0 = grid[combination[0]]
        if num0 != '0':
            if (num0 == grid[combination[1]]) and (num0 == grid[combination[2]]):
                return num0  
    return 0

#Заполяет клетку значением 
async def mark_space():
    print()

#Нажатая кнопка - поле, которое нужно заполнить
async def press_button(callback : types.CallbackQuery):
    player_id = callback.from_user.id
    game_id = await sqlite_db.sql_players_get_game_id(player_id)
    #Если игра существует
    if game_id:
        #Если очередь пользователя
        if await sqlite_db.sql_players_get_turn(player_id):
            grid = await sqlite_db.sql_games_get_grid(game_id)
            space_id = int(callback.data.split('_')[1])
            #Если клетка не занята
            if grid[space_id] == '0':
                #Вставляет в поле символ пользователя
                symbol = str(await sqlite_db.sql_players_get_symbol(player_id))
                grid = await replace_symbol(grid, space_id, symbol)
                await sqlite_db.sql_games_update_grid(game_id, grid)

                #Меняет ход игроков пользователя
                await sqlite_db.sql_players_update_turn(player_id, 0)
                rival_id = await sqlite_db.sql_players_get_rival(player_id, game_id)
                await sqlite_db.sql_players_update_turn(rival_id, 1)

                await resend_grid(player_id, rival_id)

                #Завершает игру, если нашелся победитель 
                winning_symbol = await who_won(grid)
                if winning_symbol != 0:
                    winner = await sqlite_db.sql_players_get_winner(game_id, winning_symbol)
                    loser = await sqlite_db.sql_players_get_loser(game_id, winning_symbol)
                    await end_game(winner, loser, game_id)
                #Если все клетки заполнены - ничья
                elif grid.find('0') == -1:
                    await end_game(player_id, rival_id, game_id, is_draw=True)
            else:
                await callback.answer('Эта клетка уже занята!', show_alert=True)
        else:
            await callback.answer('Не твой ход!', show_alert=True)
    else:
        await callback.answer('Эта игра уже закончена!', show_alert=True)

#Прекращает игру, делая нажавшего на кнопку - проигравшим
async def stop_game(message : types.Message):
    player_id = message.from_user.id
    game_id = await sqlite_db.sql_players_get_game_id(player_id)
    rival_id = await sqlite_db.sql_players_get_rival(player_id, game_id)
    await end_game(rival_id, player_id, game_id)

#Прекращает поиск соперника, удаляя пользователя из таблицы ожидания и удаляя сообщение с поиском
async def stop_searching(callback : types.CallbackQuery):
    player_id = callback.from_user.id
    await sqlite_db.sql_waiting_list_delete(player_id)
    await delete_game_message(player_id)
    await bot.send_message(player_id, 'Поиск прерван, что теперь?', reply_markup=keyboard_menu)


def register_handlers_game(dp : Dispatcher):
    dp.register_callback_query_handler(press_button, lambda message: 'pressed' in message.data)
    dp.register_callback_query_handler(stop_game, lambda message: 'stop_game' in message.data)
    dp.register_callback_query_handler(stop_searching, lambda message: 'stop_searching' in message.data)