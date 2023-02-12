from aiogram import types, Dispatcher
from create_bot import dp, bot

from db import sqlite_db
from handlers import game
from keyboards import keyboard_menu

#Заносит пользователя в таблицу со счетом и приветсвует его
async def command_start(message : types.Message):
    id = message.from_user.id
    await sqlite_db.sql_score_add(id)
    await bot.send_message(id, 'Привет! Готов начать игру?', reply_markup=keyboard_menu)

#Присылает статистику по играм
async def command_score(message : types.Message):
    id = message.from_user.id
    score = await sqlite_db.sql_score_get(id)
    text = f'ТВОИ ИГРЫ\n\nВыигрыши: {score[0]}\nПроигрыши: {score[1]}\nНичьи: {score[2]}\nВСЕГО ИГР: {score[0] + score[1] + score[2]}'
    await bot.send_message(id, text, reply_markup=keyboard_menu)

#Начинает поиск противника для игры
async def command_new_game(message : types.Message):
    player_id = str(message.from_user.id)
    rival_id = await sqlite_db.sql_waiting_list_get_rival()

    #Если противник - это игрок, то он уже есть в списке ожидания. 
    #Удаляем сообщение с запросом, чтобы сымитировать деятельность
    #Если его нет - ищем противника 
    if rival_id == player_id:
        await message.delete()
    else:
        await game.find_rival(player_id)

#Ответ на любые сообщения, которые не обрабатываются ботом
async def werid_message(message : types.Message):
    await message.answer('Я не понимаю. Воспользуйся встроенными кнопочками.')

def register_handlers_menu(dp : Dispatcher):
    dp.register_message_handler(command_start, commands='start')
    dp.register_message_handler(command_score, commands='my_score')
    dp.register_message_handler(command_new_game, commands='new_game')
    dp.register_message_handler(werid_message)
