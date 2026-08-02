from aiogram.fsm.state import State, StatesGroup


class TestStates(StatesGroup):
    in_progress = State()


class AppealStates(StatesGroup):
    waiting_for_text = State()


class AdminReplyStates(StatesGroup):
    waiting_for_reply = State()


class BroadcastStates(StatesGroup):
    waiting_for_message = State()
    waiting_for_confirm = State()


class AddAdminStates(StatesGroup):
    waiting_for_id = State()


class RemoveAdminStates(StatesGroup):
    waiting_for_id = State()


class AddChannelStates(StatesGroup):
    waiting_for_chat_id = State()


class AddSubjectStates(StatesGroup):
    waiting_for_name = State()


class UserStatsStates(StatesGroup):
    waiting_for_id = State()


class RemoveQuestionStates(StatesGroup):
    waiting_for_id = State()


class AddQuestionStates(StatesGroup):
    choosing_subject = State()
    waiting_question = State()
    waiting_option_a = State()
    waiting_option_b = State()
    waiting_option_c = State()
    waiting_option_d = State()
    waiting_correct = State()
