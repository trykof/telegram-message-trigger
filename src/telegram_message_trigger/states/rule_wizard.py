from aiogram.fsm.state import State, StatesGroup


class AddRuleStates(StatesGroup):
    case_sensitivity = State()
    whole_word = State()
    triggers = State()
    reply_text = State()
    scope = State()
    scope_contact = State()


class EditMatchingStates(StatesGroup):
    case_sensitivity = State()
    whole_word = State()


class EditTriggersStates(StatesGroup):
    triggers = State()


class EditReplyStates(StatesGroup):
    reply_text = State()


class EditScopeStates(StatesGroup):
    scope = State()
    scope_contact = State()
