from aiogram.fsm.state import State, StatesGroup


class AddRuleStates(StatesGroup):
    case_sensitivity = State()
    whole_word = State()
    triggers = State()
    reply_text = State()


class EditMatchingStates(StatesGroup):
    case_sensitivity = State()
    whole_word = State()


class EditTriggersStates(StatesGroup):
    triggers = State()


class EditReplyStates(StatesGroup):
    reply_text = State()
