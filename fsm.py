from aiogram.dispatcher.filters.state import State, StatesGroup

class IncreaseBalanceState(StatesGroup):
    balance = State()
    player_id = State()
    
class GameState(StatesGroup):
    word = State()
    