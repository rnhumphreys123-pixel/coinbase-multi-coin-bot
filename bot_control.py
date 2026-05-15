import json

CONTROL_FILE = "bot_control.json"


def load_control_state():
    try:
        with open(CONTROL_FILE, "r") as file:
            return json.load(file)

    except FileNotFoundError:
        default_state = {
            "bot_paused": False
        }

        save_control_state(default_state)

        return default_state


def save_control_state(state):
    with open(CONTROL_FILE, "w") as file:
        json.dump(state, file, indent=4)


def is_bot_paused():
    state = load_control_state()

    return state.get("bot_paused", False)


def set_bot_paused(paused):
    state = load_control_state()

    state["bot_paused"] = paused

    save_control_state(state)