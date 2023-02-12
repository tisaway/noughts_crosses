from aiogram.utils import executor

from create_bot import dp
from db import sqlite_db
from handlers import game, menu

async def on_startup(_):
    print('Bot is running.')
    sqlite_db.sql_start()

game.register_handlers_game(dp)
menu.register_handlers_menu(dp)

executor.start_polling(dp, skip_updates=True, on_startup=on_startup)