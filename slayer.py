import math

from subs.miniscape import users
from subs.miniscape import items
from subs.miniscape import adventures as adv
from subs.miniscape import monsters as mon

SLAYER_HEADER = ':skull_crossbones: __**SLAYER**__ :skull_crossbones:\n'


def calc_chance(userid, monsterid):
    """Calculates the chance of success of a task."""
    equipment = users.read_user(userid, key=users.EQUIPMENT_KEY)
    player_arm = users.get_equipment_stats(equipment)[2]
    monster_acc = mon.get_attr(monsterid, key=mon.ACCURACY_KEY)
    monster_dam = mon.get_attr(monsterid, key=mon.DAMAGE_KEY)
    monster_combat = mon.get_attr(monsterid, key=mon.LEVEL_KEY)
    player_combat = users.xp_to_level(users.read_user(userid, key=users.SLAYER_XP_KEY))
    if mon.get_attr(monsterid, key=mon.DRAGON_KEY) and '266' not in equipment:
        monster_base = 100
    else:
        monster_base = 1

    c = 1 + monster_combat / 200
    d = player_combat / 200
    dam_multiplier = monster_base + monster_acc / 200

    chance = round(min(600 * max(0, (player_arm / (monster_dam * dam_multiplier + c)) / 2 + d), 100))
    return chance


def calc_length(userid, monsterid, number):
    """Calculates the length of a task."""
    combat_level = users.xp_to_level(users.read_user(userid, key=users.COMBAT_XP_KEY))
    equipment = users.read_user(userid, key=users.EQUIPMENT_KEY)
    player_dam, player_acc, player_arm = users.get_equipment_stats(equipment)
    monster_arm = mon.get_attr(monsterid, key=mon.ARMOUR_KEY)
    monster_xp = mon.get_attr(monsterid, key=mon.XP_KEY)
    if mon.get_attr(monsterid, key=mon.DRAGON_KEY) and '266' not in equipment:
        monster_base = 100
    else:
        monster_base = 1

    c = combat_level
    dam_multiplier = 1 + player_acc / 200
    base_time = math.floor(number * monster_xp / 10)
    time = round(base_time * (monster_arm * monster_base / (player_dam * dam_multiplier + c)))
    return base_time, time


def calc_number(userid, monsterid, time):
    """Calculates the number of monsters that can be killed in a given time period."""
    combat_level = users.xp_to_level(users.read_user(userid, key=users.COMBAT_XP_KEY))
    equipment = users.read_user(userid, key=users.EQUIPMENT_KEY)
    player_dam, player_acc, player_arm = users.get_equipment_stats(equipment)
    monster_arm = mon.get_attr(monsterid, key=mon.ARMOUR_KEY)
    monster_xp = mon.get_attr(monsterid, key=mon.XP_KEY)
    if mon.get_attr(monsterid, key=mon.DRAGON_KEY) and '266' not in equipment:
        monster_base = 100
    else:
        monster_base = 1

    dam_multiplier = 1 + player_acc / 200

    number = math.floor((10 * time * (player_dam * dam_multiplier + combat_level)) /
                        (monster_arm * monster_base * monster_xp))
    return number


def get_kill(userid, monster, length=-1, number=-1):
    """Lets the user start killing monsters.."""
    out = f'{SLAYER_HEADER}'
    if not adv.is_on_adventure(userid):
        try:
            monsterid = mon.find_by_name(monster)
            length = int(length)
            number = int(number)
        except KeyError:
            return f'Error: {monster} is not a monster.'
        except ValueError:
            return f'Error: {length} is not a valid length of time.'
        monster_name = mon.get_attr(monsterid)
        slayer_level = users.xp_to_level(users.read_user(userid, key=users.SLAYER_XP_KEY))
        slayer_requirement = mon.get_attr(monsterid, key=mon.SLAYER_REQ_KEY)
        if slayer_level < slayer_requirement:
            return f'Error: {monster_name} has a slayer requirement ({slayer_requirement}) higher ' \
                   f'than your slayer level ({slayer_level})'

        if number > 500:
            number = 500
        if length > 180:
            length = 180

        if int(number) < 0:
            number = calc_number(userid, monsterid, length * 60)
            if number > 500:
                number = 500
        elif int(length) < 0:
            length = math.floor(calc_length(userid, monsterid, number)[1] / 60)
        else:
            return 'Error: argument missing (number or kill length).'
        grind = adv.format_line(1, userid, adv.get_finish_time(length * 60), monsterid, monster_name, number, length)
        adv.write(grind)
        out += f'You are now killing {number} {monster_name} for {length} minutes.'
    else:
        task = adv.read(userid)
        adventure_id = int(task[0])

        if adventure_id == 1:
            userid, finish_time, monsterid, monster_name, number, length = task[1:]

            try:
                time_left = 'in ' + str(adv.get_delta(finish_time)) + ' minutes'
            except ValueError:
                time_left = 'at an indeterminate time'
            out += f'You are currently killing {number} {monster_name} for {length} minutes. ' \
                   f'You can see your loot {time_left}.'
        else:
            out += adv.print_on_adventure_error('kill')
    return out


def get_kill_result(person, *args):
    """Determines the loot of a monster grind."""
    try:
        monsterid, monster_name, num_to_kill, length = args[0]
    except ValueError as e:
        print(e)
        raise ValueError
    out = ''
    loot = mon.get_loot(monsterid, int(num_to_kill))
    users.update_inventory(person.id, loot)
    out += print_loot(loot, person, monster_name, num_to_kill)
    xp_gained = mon.get_attr(monsterid, key=mon.XP_KEY) * int(num_to_kill)
    users.update_user(person.id, xp_gained, users.COMBAT_XP_KEY)
    combat_xp_formatted = '{:,}'.format(xp_gained)
    out += f'\nYou have also gained {combat_xp_formatted} combat xp.'
    return out


def get_result(person, *args):
    """Determines the success and loot of a slayer task."""
    try:
        monsterid, monster_name, num_to_kill, chance = args[0]
    except ValueError as e:
        print(e)
        raise ValueError
    out = ''
    if adv.is_success(calc_chance(person.id, monsterid)):
        loot = mon.get_loot(monsterid, int(num_to_kill))
        users.update_inventory(person.id, loot)
        out += print_loot(loot, person, monster_name, num_to_kill)
        xp_gained = mon.get_attr(monsterid, key=mon.XP_KEY) * int(num_to_kill)
        users.update_user(person.id, xp_gained, users.SLAYER_XP_KEY)
        users.update_user(person.id, round(0.7 * xp_gained), users.COMBAT_XP_KEY)
        slayer_xp_formatted = '{:,}'.format(xp_gained)
        combat_xp_formatted = '{:,}'.format(round(0.7 * xp_gained))
        out += f'\nYou have also gained {slayer_xp_formatted} slayer xp and {combat_xp_formatted} combat xp.'
    else:
        xp_gained = round(mon.get_attr(monsterid, key=mon.XP_KEY) * int(num_to_kill) / 4)
        users.update_user(person.id, xp_gained, users.SLAYER_XP_KEY)
        users.update_user(person.id, round(0.7 * xp_gained), users.COMBAT_XP_KEY)
        slayer_xp_formatted = '{:,}'.format(xp_gained)
        combat_xp_formatted = '{:,}'.format(round(0.7 * xp_gained))
        out += f'{person.mention}, your slayer task of {num_to_kill} {monster_name} has failed.\n'\
               f'You have received {slayer_xp_formatted} slayer xp and {combat_xp_formatted} combat xp.'
    return out


def get_task_info(userid):
    """Gets the info associated with a user's slayer task and returns it as a tuple."""
    task = adv.read(userid)
    taskid, userid, finish_time, monsterid, monster_name, num_to_kill, chance = task

    time_left = adv.get_delta(finish_time)

    return taskid, userid, time_left, monsterid, monster_name, num_to_kill, chance


def get_task(userid):
    """Assigns a user a slayer task provided they are not in the middle of another adventure."""
    out = SLAYER_HEADER
    if not adv.is_on_adventure(userid):
        for _ in range(1000):
            monsterid = mon.get_random(slayer_level=users.xp_to_level(users.read_user(userid, key=users.SLAYER_XP_KEY)))
            num_to_kill = mon.get_task_length(monsterid)
            equipment = users.read_user(userid, key=users.EQUIPMENT_KEY)

            base_time, task_length = calc_length(userid, monsterid, num_to_kill)
            chance = calc_chance(userid, monsterid)
            # print(f'{monsterid} {task_length/base_time} {chance}')
            if 0.5 <= task_length / base_time <= 2 and chance >= 20 \
                    and mon.get_attr(monsterid, key=mon.SLAYER_KEY) is True:
                break
        else:
            return "Error: gear too low to fight any monsters. Please equip some better gear and try again. " \
                   "If you are new, type `~starter` to get a bronze kit."
        monster_name = mon.get_attr(monsterid)
        task = adv.format_line(0, userid, adv.get_finish_time(task_length), monsterid,
                               monster_name, num_to_kill, chance)
        adv.write(task)
        out += print_task(userid)
    else:
        task = adv.read(userid)
        adventure_id = int(task[0])

        if adventure_id == 0:
            userid, finish_time, monsterid, monster_name, num_to_kill, chance = task[1:]

            try:
                time_left = 'in ' + str(adv.get_delta(finish_time)) + ' minutes'
            except ValueError:
                time_left = 'at an indeterminate time'
            chance = calc_chance(userid, monsterid)
            out += f'You are already on a slayer task. You can see the results of your task of {num_to_kill} ' \
                   f'{monster_name} {time_left}. You currently have a {chance}% of succeeding with your current gear.'
        else:
            out += adv.print_on_adventure_error('task')
    return out


def print_loot(loot, person, monster_name, num_to_kill, add_mention=True):
    """Converts a user's loot from a slayer task to a string."""
    out = f'{SLAYER_HEADER}**'
    if add_mention:
        out += f'{person.mention}, '
    else:
        out += f'{person.name}, '

    out += f'Your loot from your {num_to_kill} {monster_name} has arrived!**\n'

    for key in loot.keys():
        out += f'{loot[key]} {items.get_attr(key)}\n'

    total_value = '{:,}'.format(users.get_value_of_inventory(loot))
    out += f'*Total value: {total_value}*'

    return out


def print_task(userid):
    """Converts a user's task into a string."""
    taskid, userid, task_length, monsterid, monster_name, num_to_kill, chance = get_task_info(userid)

    out = f'New Slayer task received: Kill __{num_to_kill} {monster_name}__!\n'
    out += f'This will take {task_length} minutes '
    out += f'and has a success rate of {chance}% with your current gear. '
    return out
