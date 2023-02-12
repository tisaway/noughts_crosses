from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

#Inline кнопка отмены при ожидании игрока
button_stopsearching = InlineKeyboardButton('Прекратить поиск', callback_data='/stop_searching')
keyboard_searching = InlineKeyboardMarkup(resize_keyboard=True).add(button_stopsearching)

#Получает на вход строку grid в формате "000000000" и преобразует в inline кнопки
async def get_grid_buttons(grid):
    buttons = []
    i = 0
    for space in grid:
        match space:
            case '0':
                text = ' '
            case '1':
                text = '⭕️'
            case '2':
                text = '❌'
        command = 'pressed_' + str(i)
        i += 1
        buttons.append(InlineKeyboardButton(text, callback_data=command))
    buttons.append(InlineKeyboardButton('Прервать игру?', callback_data='/stop_game'))
    return buttons

#Возвращает inline клавиатуру игрового поля
async def keyboard_get_qrid(grid):
    b = await get_grid_buttons(grid)
    return InlineKeyboardMarkup(resize_keyboard=True).row(b[0], b[1], b[2]).row(b[3], b[4], b[5]).row(b[6], b[7], b[8]).add(b[9])
