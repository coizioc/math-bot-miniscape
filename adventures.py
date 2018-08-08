import datetime
import math
import random

from subs.miniscape import quests, slayer, craft, clues
from subs.miniscape.files import ADVENTURES_FILE

# An adventure in the adventure file is stored as the following (with semicolon delimiters in between):
# adventureid, userid, completion_time, *args
# where *args represent adventure-specific arguments.

ON_ADVENTURE_ERROR = 'You are currently in the middle of something. Please finish that before starting something else.'


def add(adventure_id, userid, *args):
    """Adds an adventure to a file."""
    args_str = [str(arg) for arg in args]
    out = f'{adventure_id};{userid};$TIME;'
    out += f"{';'.join(args_str)}\n"
    write(out)


def add_finish_time(userid, time):
    """Adds a datetime to a previously added adventure."""
    adventures = [adventure.replace('$TIME', time) for adventure in get_list() if str(userid) in adventure]
    write('\n'.join(adventures), overwrite=True)


def format_line(*args):
    args_str = [str(arg) for arg in args]
    return ';'.join(args_str) + '\n'


def get_adventure(userid):
    lines = get_list()
    for line in lines:
        if str(userid) in line:
            return line.split(';')
    else:
        raise NameError


def get_delta(finish_time):
    """Calculates the time remaining until a task is finished in minutes."""
    try:
        finish_time = datetime.datetime.strptime(finish_time, '%Y-%m-%d %H:%M:%S.%f')
    except ValueError:
        raise ValueError
    current_time = datetime.datetime.now()
    delta = finish_time - current_time
    return math.floor(delta.total_seconds() / 60)


def get_finish_time(task_length):
    """Calculates the time when an adventure is over given its length."""
    return datetime.datetime.now() + datetime.timedelta(seconds=task_length)


def get_finished():
    """Gets a list of adventureswith time preceding the current time, removes those from the adventure file,
    and returns the list of finished adventures."""
    adventures = get_list()
    finished_adventures = []
    current_time = datetime.datetime.now()
    out = ''
    for adventure in adventures:
        adventure_args = adventure.split(';')
        time = adventure_args[2]
        finish_time = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S.%f')
        if finish_time < current_time:
            finished_adventures.append(adventure_args)
        else:
            out += f'{adventure}\n'
    write(out, overwrite=True)
    return finished_adventures


def get_list():
    """Opens the adventures file and returns a list of adventures."""
    with open(ADVENTURES_FILE, 'r') as f:
        lines = f.read().splitlines()
    return lines


def is_on_adventure(userid):
    """Determines whether a user is already on/is preparing for an adventure."""
    adventures = get_list()

    for adventure in adventures:
        if str(userid) in adventure:
            return True
    else:
        return False


def is_success(chance):
    """Determines whether an adventure is successful or not."""
    if random.randint(0, 100) <= int(chance):
        return True
    else:
        return False


def print_adventure(userid):
    lines = get_list()

    for line in lines:
        if str(userid) in line:
            adventure = line.split(';')
            break
    else:
        raise KeyError
    adventureid, userid, finish_time = adventure[0:3]
    adventures = {
        '0': slayer.print_status,
        '1': slayer.print_kill_status,
        '2': quests.print_status,
        '3': craft.print_status,
        '4': clues.print_status
    }
    time_left = get_delta(finish_time)
    if time_left == 1:
        time_string = 'in 1 minute'
    elif time_left < 1:
        time_string = '   soon'
    else:
        time_string = f'in {time_left} minutes'
    out = adventures[adventureid](time_string, adventure[3:])
    return out


def print_on_adventure_error(adventure):
    """Prints a string saying that the user cannot do two adventures at once."""
    out = f'Please finish that first before starting a new {adventure}.'
    return out


def read(userid):
    """Finds an adventure from a userid and returns the values of the adventure as a list."""
    userid = str(userid)
    adventures = get_list()

    for adventure in adventures:
        if userid in adventure:
            return adventure.split(';')
    else:
        raise ValueError


def remove(userid):
    """Removes an adventure from the adventures file containing the userid."""
    userid = str(userid)
    new_adventures = [adventure for adventure in get_list() if userid not in adventure]
    write('\n'.join(new_adventures) + '\n', overwrite=True)


def write(data, overwrite=False):
    """Writes/Appends a string representing adventures to the adventure file."""
    operation = 'w+' if overwrite else 'a+'

    with open(ADVENTURES_FILE, operation) as f:
        f.write(data)
