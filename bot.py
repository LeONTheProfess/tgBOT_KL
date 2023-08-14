from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher.filters import Text
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup
from aiogram_calendar import simple_cal_callback, SimpleCalendar, dialog_cal_callback, DialogCalendar

from config import TOKEN, whitelist
from messages import MESSAGES
from utils import ClientStates, Reports


bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

start_kb = ReplyKeyboardMarkup(resize_keyboard=True,)
start_kb.row('Биллинг')

back_kb = ReplyKeyboardMarkup(resize_keyboard=True,)
back_kb.row('⬅️Назад')


@dp.message_handler(lambda message: message.chat.id not in whitelist)
async def checker(message):
   await message.answer("Вы не находитесь в Whitelist!")

@dp.message_handler(Text(equals=['⬅️Назад'], ignore_case=True), state='*')
async def billing_handler(message: Message):
    state = dp.current_state(chat=message.chat.id)
    await state.reset_state()
    return await message.answer(
        'Возврат к главному меню!', 
        reply_markup=start_kb)

# Вывод календаря для выбора даты-начала 
@dp.callback_query_handler(dialog_cal_callback.filter(), state=ClientStates.CHOOSE_FIRST_DATE)
async def process_dialog_calendar_first(callback_query: CallbackQuery, callback_data: dict):
    selected, date = await DialogCalendar().process_selection(callback_query, callback_data)
    state = dp.current_state(chat=callback_query.message.chat.id)
    user_data = await state.get_data()
    if selected:
        await state.set_state(ClientStates.CHOOSE_SECOND_DATE)
        await callback_query.message.answer(
            f'Вы выбрали дату начала {date.strftime("%d/%m/%Y")} для отчёта {user_data["report"]}',
            reply_markup=back_kb
        )
        return await callback_query.message.answer(MESSAGES['input_second_date'], reply_markup=await DialogCalendar().start_calendar())


# Вывод календаря для выбора даты-конца 
@dp.callback_query_handler(dialog_cal_callback.filter(), state=ClientStates.CHOOSE_SECOND_DATE)
async def process_dialog_calendar_second(callback_query: CallbackQuery, callback_data: dict):
    selected, date = await DialogCalendar().process_selection(callback_query, callback_data)
    state = dp.current_state(chat=callback_query.message.chat.id)
    user_data = await state.get_data()
    if selected:
        await state.reset_state()
        await callback_query.message.answer(
            f'Вы выбрали дату окончания {date.strftime("%d/%m/%Y")} для отчёта {user_data["report"]}',
            reply_markup=start_kb
        )
        return await callback_query.message.answer_document(open("./reports/billing.html", "rb"))

@dp.message_handler(Text(equals=['Биллинг'], ignore_case=True))
async def billing_handler(message: Message):
    state = dp.current_state(chat=message.chat.id)
    await state.reset_state()
    await state.set_state(ClientStates.CHOOSE_FIRST_DATE)
    await state.update_data(report=Reports.BILLING)
    await message.answer(
        'Выбран отчёт Биллинг', 
        reply_markup=back_kb)
    return await message.answer(
        MESSAGES['input_first_date'], 
        reply_markup=await DialogCalendar().start_calendar())


    

@dp.message_handler(commands=['start'])
async def cmd_start(message: Message):
    state = dp.current_state(chat=message.chat.id)
    await state.reset_state()
    await message.reply(MESSAGES['start'], reply_markup=start_kb)


@dp.message_handler(commands=['help'], state='*')
async def process_help_command(message: types.Message):    
    state = dp.current_state(chat=message.chat.id)
    await state.reset_state()
    await message.reply(MESSAGES['help'], reply_markup=start_kb)

@dp.message_handler()
async def echo_message(msg: types.Message):
    await bot.send_message(msg.from_user.id, MESSAGES['not_understand'])

async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()

if __name__ == '__main__':
    executor.start_polling(dp, on_shutdown=shutdown, skip_updates=True)