import json
import aiofiles
from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import *
from settings import *
from fsm import *
from wordle_module import wordle, utils
import datetime
from io import BytesIO
import asyncio
import aioschedule

class PushState(StatesGroup):
    input_for_push = State()
    input_file = State()
    input_pic = State()
    wait = State()
    preview = State()

class EditPush(StatesGroup):
    edit_text = State()
    edit_file = State()
    edit_pic = State()
    wait = State()

words = [
    'герой',
    'школа', 
    'булка',
    'юноша',
    'глыба',
    'глыба',
    'глыба',
    'глыба'
]
last_images = {}

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

@dp.message_handler(commands=['start'])
async def start(message: Message, state: FSMContext):
    if str(message.from_user.id) in ADMINS_ID:
        await message.answer('Добрый день, админ!')
    else:
        id = await new_player(message.from_user.id)
        await message.answer(f'''
Привет 🥐

Спасибо, что участвуешь в наших мероприятиях!

За участие в каждом ты будешь получать ХЛЕБИКИ (ХБ) - нашу валюту, которые сможешь потратить на ярмарке в день самоуправления (:
Хлебики начисляются КАЖДЫЙ раз при участии, а при ПОБЕДЕ их количество УДВАИВАЕТСЯ!

Чтобы тебе ничего не пропустить, мы будем присылать краткую информацию о последующих событиях!

Участвуй в каждом, чтобы собрать как можно больше наклеек нашего ХЛЕБНОГО ПАССА и получить ГЛАВНЫЙ ПРИЗ!

Твой номер игрока: {id}

А теперь ты можешь начинать участовать в конкурсах 🫶🏻''')

@dp.message_handler(commands=['balance'])
async def start(message: Message, state: FSMContext):
    if str(message.from_user.id) in ADMINS_ID:
        await message.answer('Добрый день, админ!')
    else:
        user = await get_player(message.from_user.id)
        await message.answer(f'''
Твой баланс: {user["balance"]} ХБ
Продолжай в том же духе!''')

@dp.message_handler(commands=['id'])
async def start(message: Message, state: FSMContext):
    if str(message.from_user.id) in ADMINS_ID:
        await message.answer('Добрый день, админ!')
    else:
        user = await get_player(message.from_user.id)
        await message.answer(f'''
Твой номер игрока: {user["id"]}
''')

@dp.message_handler(commands=['comp'])
async def competition(message: Message, state: FSMContext):
    if str(message.from_user.id) not in ADMINS_ID:
        await message.answer('Вы не участник сообщества 11-2 team!')
        return
    await message.answer('Введите номер игрока:')
    await state.set_state(IncreaseBalanceState.player_id)

async def pushText(message: Message, state: FSMContext):
    if str(message.from_user.id) not in ADMINS_ID:
        await message.answer('Вы не участник сообщества 11-2 team!')
        return
    await message.answer("Введите текст для пуша")
    await state.set_state(PushState.input_for_push)
    await state.update_data( text = None )
    await state.update_data( photo = None )
    await state.update_data( file = None )

async def pre_push(message: Message, state: FSMContext):
    data = await state.get_data()
    text = data.get( 'text' )
    photo  = data.get( 'photo' )
    file = data.get( 'file' )

    kb = InlineKeyboardMarkup()

    if photo == None:
        kb.add(InlineKeyboardButton('Добавить фото', callback_data="add_pic"))
    if file == None:
        kb.add(InlineKeyboardButton('Добавить файл', callback_data="add_file"))
    if photo != None:
        kb.add(InlineKeyboardButton('Удалить фото', callback_data="del_pic"))
    if file != None:
        kb.add(InlineKeyboardButton('Удалить файл', callback_data="del_file"))

    kb.add(InlineKeyboardButton('Отменить рассылку', callback_data="cancel_push"))
    kb.add(InlineKeyboardButton('Отправить рассылку', callback_data="send_push"))
    
    print( photo )
    await message.answer(f"Предварительный вид сообщения\n")
    if photo ==  None and file==None:
        await message.answer(f"{text}", reply_markup=kb)
    elif photo != None and file == None:
        await bot.send_photo(message.chat.id, photo, caption=text, reply_markup=kb)
    elif photo == None and file != None:
        await bot.send_document(message.chat.id, file, caption=text, reply_markup=kb)
    else:
        await bot.send_photo(message.chat.id, photo, caption=text)
        await bot.send_document(message.chat.id, file, reply_markup=kb)
        
    

async def getText(message: Message, state: FSMContext):
    await state.update_data(text = message.text)
    await pre_push( message, state )
    await state.set_state(PushState.preview)



async def add_pic(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Отправьте картинку.', show_alert=True)
    await state.set_state(PushState.input_pic)

async def add_file(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Отправьте картинку.', show_alert=True)
    await state.set_state(PushState.input_file)


async def pushPic(message: Message, state: FSMContext):
    if message.photo:
        await state.update_data(photo = message.photo[-1].file_id)
        await pre_push( message, state )
        await state.set_state(PushState.preview)
    else:
        await message.answer("Ошибка данных. Отправьте картинку как фотографию")

async def pushFile(message: Message, state: FSMContext):
    if message.document:
        await state.update_data(file = message.document.file_id)
        await pre_push( message, state )
        await state.set_state(PushState.preview)
    else:
        await message.answer("Ошибка данных. Отправьте файл")
 

async def cancel_push(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.reset_state()
    await state.reset_data()
    await state.reset_state()
    await callback.message.answer("Рассылка отменена")

async def send_push(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    photo = data.get('photo')
    file = data.get('file')
    text = data.get('text')

    # используйте конструкцию и предварительного просмотра
    # картинка, текст и файл должны отправляться единым целым как в предпросмотре
    if photo ==  None and file==None:
        for i in await get_all_tg_users():
            try: await bot.send_message(i[0], f"{text}")
            except: pass
    elif photo != None and file == None:
        for i in await get_all_tg_users():
            try: await bot.send_photo(i[0], photo, caption=text)
            except: pass
    elif photo == None and file != None:
        for i in await get_all_tg_users():
            try: await bot.send_document(i[0], file, caption=text)
            except: pass
    else:
        for i in await get_all_tg_users():
            try:
                await bot.send_photo(i[0], photo, caption=text)
                await bot.send_document(i[0], file)
            except: pass
    await state.reset_state()
    await callback.answer("Рассылка отправлена!")

async def view_push(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    photo = data.get('photo')
    file = data.get('file')
    text = data.get('text')
    if photo:
        await bot.send_photo(callback.from_user.id, photo, caption=text)
    if file:
        await bot.send_document(callback.from_user.id, file, caption=text)
    if not file and not photo:
        await bot.send_message(callback.from_user.id, text)

async def del_photo(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    photo = data.get('photo')
    if photo != None:
        await state.update_data(photo = None)
    await callback.answer('Фото удалено')
    await pre_push(callback.message, state)

async def del_file(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    file = data.get('file')
    if file != None:
        await state.update_data(file = None)
    await callback.answer('Файл удален')
    await pre_push(callback.message, state)



@dp.message_handler(state=IncreaseBalanceState.player_id)
async def process_player_id(message: Message, state: FSMContext):
    await state.update_data(player_id = message.text)
    await message.answer('Введите сумму, на который вы хотите пополнить баланс:')
    await state.set_state(IncreaseBalanceState.balance)

@dp.message_handler(state=IncreaseBalanceState.balance)
async def process_balance(message: Message, state: FSMContext):
    player_id = (await state.get_data())['player_id']
    balance = int(message.text)
    await state.finish()
    player = await get_player_by_player_id(player_id)
    if player == False:
        await message.answer('Пользователя с таким player_id не существует')
    await increase_balance(player_id, money=balance)
    await message.answer('Баланс успешно пополнен!')
    await bot.send_message(int(player['user_id']), f'Ваш баланс пополнен на {balance} ХБ!')

@dp.message_handler(commands=['play'])
async def play(message: Message, state: FSMContext):
    if datetime.date.today().weekday() > 4:
        await message.answer('Акция закончилась, спасибо, что были с нами!')
        return
    if str(message.from_user.id) in ADMINS_ID:
        await message.answer('Вы админ, а не игрок!')
        return
    if not await can_play(message.from_user.id):
        await message.answer('У вас закончились все попопытки на сегодня, приходите завтра!')
        return
    await message.answer('Правила очень просты: игроку дается пять попыток угадать слово. Любое слово должно быть введено в верхней строке. Если буква угадана правильно и находится в правильном месте, она будет выделена зеленым цветом, если буква есть в слове, но не в том месте, то желтым, а если буквы нет в слове, останется серым.')
    await message.answer('Отгадайте слово!')
    await state.set_state(GameState.word)

@dp.message_handler(state=GameState.word)
async def process_word(message: Message, state: FSMContext):
    player = await get_player(message.from_user.id)
    if len(message.text) != 5:
        await message.answer('В введённом слове не 5 букв, введите новое')
        await state.set_state(GameState.word)
        return
    obj = wordle.Main(limg=last_images.get(message.from_user.id),attemps_already=5-player['attemps'], target_word=words[datetime.date.today().weekday()],colormap = ["#fff", "#c0bcbc", "#14b31c", "#d4bd11", "#fff"], font_size = 45)
    result = obj.check(message.text.lower())
    last_images[message.from_user.id] = result['image']
    bio = BytesIO()
    bio.name = 'image.jpeg'
    result['image'].img.save(bio, 'JPEG')
    bio.seek(0)
    await bot.send_photo(message.from_user.id, photo=bio)
    if result['is_correct']:
        await update_attemps(player['id'], 0)
        await increase_balance(player['id'], 50)
        await message.answer('Вы отгадали слово, вам начислено 50 ХБ! Спасибо за игру! Возращайтесь завтра!')
        await state.finish()
    else:
        await decrement_attemps(player_id=player['id'])
        if not await can_play(message.from_user.id):
            await message.answer(f'К сожалению, вы не отгадали слово(\nБыло загадано слово {words[datetime.date.today().weekday()]}. Спасибо за игру! Возвращаётесь завтра!')
            await state.finish()
            return
        await message.answer(f'У вас осталось {player["attemps"]-1}. Введите другое слово')
        await state.set_state(GameState.word)    

async def is_user_exist(user_id):
    data = []
    async with aiofiles.open('players.json', 'r', encoding='utf-8') as fp:
        data = json.loads(await fp.read())
    for i in data:
        if i['user_id'] == str(user_id):
            return i
    return False

async def new_player(user_id):
    data = []
    async with aiofiles.open('players.json', 'r', encoding='utf-8') as fp:
        data = json.loads(await fp.read())
    id = len(data) + 1
    if id < 10:
        id = f'00{id}'
    elif id < 100:
        id = f'0{id}'
    else:
        id = str(id)
    data.append({
        'id': id,
        'user_id': str(user_id),
        'balance': 0,
        'attemps': 5
    })
    async with aiofiles.open('players.json', 'w', encoding='utf-8') as fp:
        await fp.write(json.dumps(data, ensure_ascii=False))
    return id

async def get_player(user_id):
    data = []
    async with aiofiles.open('players.json', 'r', encoding='utf-8') as fp:
        data = json.loads(await fp.read())
    for i in data:
        if str(i['user_id']) == str(user_id):
            return i
    return False

async def get_player_by_player_id(player_id):
    data = []
    async with aiofiles.open('players.json', 'r', encoding='utf-8') as fp:
        data = json.loads(await fp.read())
    for i in data:
        if str(i['id']) == str(player_id):
            return i
    return False

async def increase_balance(player_id, money):
    data = []
    async with aiofiles.open('players.json', 'r', encoding='utf-8') as fp:
        data = json.loads(await fp.read())
    for n, i in enumerate(data):
        if str(i['id']) == str(player_id):
            data[n]['balance'] += money
            break
    async with aiofiles.open('players.json', 'w', encoding='utf-8') as fp:
        await fp.write(json.dumps(data, ensure_ascii=False))

async def update_attemps(player_id, new_attemps):
    data = []
    async with aiofiles.open('players.json', 'r', encoding='utf-8') as fp:
        data = json.loads(await fp.read())
    for n, i in enumerate(data):
        if str(i['id']) == str(player_id):
            data[n]['attemps'] = new_attemps
            break
    async with aiofiles.open('players.json', 'w', encoding='utf-8') as fp:
        await fp.write(json.dumps(data, ensure_ascii=False))

async def decrement_attemps(player_id):
    data = []
    async with aiofiles.open('players.json', 'r', encoding='utf-8') as fp:
        data = json.loads(await fp.read())
    for n, i in enumerate(data):
        if str(i['id']) == str(player_id):
            data[n]['attemps'] -= 1
            break
    async with aiofiles.open('players.json', 'w', encoding='utf-8') as fp:
        await fp.write(json.dumps(data, ensure_ascii=False))

async def can_play(user_id):
    data = []
    async with aiofiles.open('players.json', 'r', encoding='utf-8') as fp:
        data = json.loads(await fp.read())
    for n, i in enumerate(data):
        if str(i['user_id']) == str(user_id):
            if i['attemps'] < 1: return False
            else: return True
            
    async with aiofiles.open('players.json', 'w', encoding='utf-8') as fp:
        await fp.write(json.dumps(data, ensure_ascii=False))

async def reset_attemps():
    data = []
    async with aiofiles.open('players.json', 'r', encoding='utf-8') as fp:
        data = json.loads(await fp.read())
    for n, i in enumerate(data):
        data[n]['attemps'] = 5
    async with aiofiles.open('players.json', 'w', encoding='utf-8') as fp:
        await fp.write(json.dumps(data, ensure_ascii=False))

async def get_all_tg_users():
    data = []
    users = []
    async with aiofiles.open('players.json', 'r', encoding='utf-8') as fp:
        data = json.loads(await fp.read())
    for n, i in enumerate(data):
        users.append(int(i['user_id']))
            

async def sender():
    data = []
    async with aiofiles.open('players.json', 'r', encoding='utf-8') as fp:
        data = json.loads(await fp.read())
    for n, i in enumerate(data):
        if i['attemps'] == 5:
            await bot.send_message(int(i['user_id']), 'У тебя ещё осталось 5 попыток в игре, не упусти шанс заработать ХЛЕБИКИ)\nЧтобы поиграть просто нажми /play')

async def scheduler():
    aioschedule.every(1).day.at('00:00').do(reset_attemps)
    aioschedule.every(1).day.at('12:00').do(sender)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)

async def on_start(_):
    dp.register_message_handler(pushText, lambda message: message.text == '/push')
    dp.register_message_handler(getText, state=PushState.input_for_push, content_types=ContentType.ANY)
    dp.register_message_handler(pushFile, state=PushState.input_file, content_types=ContentType.ANY)
    dp.register_message_handler(pushPic, state=PushState.input_pic, content_types=ContentType.ANY)
    dp.register_callback_query_handler(cancel_push, lambda callback: callback.data == 'cancel_push', state=PushState.wait)
    dp.register_callback_query_handler(send_push, lambda callback: callback.data == 'send_push', state=PushState.preview)
    dp.register_callback_query_handler(view_push, lambda callback: callback.data == 'view_push', state=PushState.wait)

    dp.register_callback_query_handler(cancel_push, lambda callback: callback.data == 'cancel_push', state=PushState.preview)
    dp.register_callback_query_handler(add_pic, lambda callback: callback.data == 'add_pic', state=PushState.preview)
    dp.register_callback_query_handler(add_file, lambda callback: callback.data == 'add_file', state=PushState.preview)

    dp.register_callback_query_handler(del_photo, lambda callback: callback.data == 'del_pic', state=PushState.preview)
    dp.register_callback_query_handler(del_file, lambda callback: callback.data == 'del_file', state=PushState.preview)
    asyncio.create_task(scheduler())

executor.start_polling(dp, skip_updates=True, on_startup=on_start)