import math
import datetime

from subs.miniscape.files import XP_FACTOR
from subs.miniscape import adventures as adv
from subs.miniscape import items
from subs.miniscape import monsters as mon
from subs.miniscape import users

SLAYER_HEADER = ':skull_crossbones: __**SLAYER**__ :skull_crossbones:\n'


def calc_chance(userid, monsterid, number):
    """Calculates the chance of success of a task."""

    equipment = users.read_user(userid, key=users.EQUIPMENT_KEY)
    player_arm = users.get_equipment_stats(equipment)[2]
    monster_acc = mon.get_attr(monsterid, key=mon.ACCURACY_KEY)
    monster_dam = mon.get_attr(monsterid, key=mon.DAMAGE_KEY)
    monster_combat = mon.get_attr(monsterid, key=mon.LEVEL_KEY)
    player_combat = users.xp_to_level(users.read_user(userid, key=users.SLAYER_XP_KEY))
    number = int(number)
    if mon.get_attr(monsterid, key=mon.DRAGON_KEY):
        if equipment['7'] == '266' or equipment['7'] == '293':
            monster_base = 1
        else:
            monster_base = 100
    else:
        monster_base = 1

    player_potion = equipment['15']
    if player_potion == '429' or player_potion == '430':
        player_arm = player_arm * 1.1 + 3
    if player_potion == '433' or player_potion == '434':
        player_arm = player_arm * 1.15 + 5

    c = 1 + monster_combat / 200
    d = 1 + player_combat / 99
    dam_multiplier = monster_base + monster_acc / 200
    chance = round(min(100 * max(0, (2 * d * player_arm) / (number / 50 * monster_dam * dam_multiplier + c)), 100))
    return chance


def calc_length(userid, monsterid, number):
    """Calculates the length of a task."""
    combat_level = users.xp_to_level(users.read_user(userid, key=users.COMBAT_XP_KEY))
    equipment = users.read_user(userid, key=users.EQUIPMENT_KEY)
    player_dam, player_acc, player_arm = users.get_equipment_stats(equipment)
    monster_arm = mon.get_attr(monsterid, key=mon.ARMOUR_KEY)
    monster_xp = mon.get_attr(monsterid, key=mon.XP_KEY)
    if mon.get_attr(monsterid, key=mon.DRAGON_KEY) == 1:
        if equipment['7'] == '266' or equipment['7'] == '293':
            monster_base = 1
        else:
            monster_base = 100
    else:
        monster_base = 1

    player_potion = equipment['15']
    if player_potion == '427' or player_potion == '430':
        player_acc = player_acc * 1.1 + 3
    if player_potion == '428' or player_potion == '430':
        player_dam = player_dam * 1.1 + 3
    if player_potion == '429' or player_potion == '430':
        player_arm = player_arm * 1.1 + 3
    if player_potion == '431' or player_potion == '434':
        player_acc = player_acc * 1.15 + 5
    if player_potion == '432' or player_potion == '434':
        player_dam = player_dam * 1.15 + 5
    if player_potion == '433' or player_potion == '434':
        player_arm = player_arm * 1.15 + 5

    c = combat_level
    dam_multiplier = 1 + player_acc / 200
    base_time = math.floor(number * monster_xp / 10)
    time = round(base_time * monster_arm * monster_base / (player_dam * dam_multiplier + c))
    return base_time, time


def calc_number(userid, monsterid, time):
    """Calculates the number of monsters that can be killed in a given time period."""
    combat_level = users.xp_to_level(users.read_user(userid, key=users.COMBAT_XP_KEY))
    equipment = users.read_user(userid, key=users.EQUIPMENT_KEY)
    player_dam, player_acc, player_arm = users.get_equipment_stats(equipment)
    monster_arm = mon.get_attr(monsterid, key=mon.ARMOUR_KEY)
    monster_xp = mon.get_attr(monsterid, key=mon.XP_KEY)
    if mon.get_attr(monsterid, key=mon.DRAGON_KEY) and '266' not in equipment:
        if equipment['7'] == '266' or equipment['7'] == '293':
            monster_base = 1
        else:
            monster_base = 100
    else:
        monster_base = 1

    player_potion = equipment['15']
    if player_potion == '427' or player_potion == '430':
        player_acc = player_acc * 1.1 + 3
    if player_potion == '428' or player_potion == '430':
        player_dam = player_dam * 1.1 + 3
    if player_potion == '429' or player_potion == '430':
        player_arm = player_arm * 1.1 + 3
    if player_potion == '431' or player_potion == '434':
        player_acc = player_acc * 1.15 + 5
    if player_potion == '432' or player_potion == '434':
        player_dam = player_dam * 1.15 + 5
    if player_potion == '433' or player_potion == '434':
        player_arm = player_arm * 1.15 + 5

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

        completed_quests = users.get_completed_quests(userid)
        quest_req = mon.get_attr(monsterid, key=mon.QUEST_REQ_KEY)
        if not {quest_req}.issubset(completed_quests) and quest_req != 0:
            return f'Error: you do not have the required quests to kill this monster.'

        monster_name = mon.get_attr(monsterid)
        slayer_level = users.xp_to_level(users.read_user(userid, key=users.SLAYER_XP_KEY))
        slayer_requirement = mon.get_attr(monsterid, key=mon.SLAYER_REQ_KEY)
        if slayer_level < slayer_requirement:
            return f'Error: {monster_name} has a slayer requirement ({slayer_requirement}) higher ' \
                   f'than your slayer level ({slayer_level})'
        if number > 1000 and slayer_level == 99:
            number = 1000
        if number > 500 and slayer_level < 99:
            number = 500
        if length > 180:
            length = 180

        if int(number) < 0:
            number = calc_number(userid, monsterid, (length + 1) * 60) - 1
            if number > 1000 and slayer_level == 99:
                number = 1000
            if number > 500 and slayer_level < 99:
                number = 500
        elif int(length) < 0:
            length = math.floor(calc_length(userid, monsterid, number)[1] / 60)
        else:
            return 'Error: argument missing (number or kill length).'
        grind = adv.format_line(1, userid, adv.get_finish_time(length * 60), monsterid, monster_name, number, length)
        adv.write(grind)
        out += f'You are now killing {number} {mon.add_plural(monsterid)} for {length} minutes.'
    else:
        out = adv.print_adventure(userid)
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
    users.add_counter(person.id, monsterid, num_to_kill)
    if mon.get_attr(monsterid, key=mon.SLAYER_KEY):
        factor = 0.75
    else:
        factor = 1

    factor *= items.get_luck_factor(person.id)
    loot = mon.get_loot(monsterid, int(num_to_kill), factor=factor)
    users.update_inventory(person.id, loot)
    out += print_loot(loot, person, monster_name, num_to_kill)

    xp_gained = mon.get_attr(monsterid, key=mon.XP_KEY) * int(num_to_kill)
    cb_level_before = users.xp_to_level(users.read_user(person.id, users.COMBAT_XP_KEY))
    users.update_user(person.id, xp_gained, users.COMBAT_XP_KEY)
    cb_level_after = users.xp_to_level(users.read_user(person.id, users.COMBAT_XP_KEY))

    combat_xp_formatted = '{:,}'.format(xp_gained)
    out += f'\nYou have also gained {combat_xp_formatted} combat xp'
    if cb_level_after > cb_level_before:
        out += f' and {cb_level_after - cb_level_before} combat levels'
    out += '.'
    users.remove_potion(person.id)

    return out


def get_result(person, *args):
    """Determines the success and loot of a slayer task."""
    try:
        monsterid, monster_name, num_to_kill, chance = args[0]
    except ValueError as e:
        print(e)
        raise ValueError
    out = ''
    users.add_counter(person.id, monsterid, num_to_kill)
    if adv.is_success(calc_chance(person.id, monsterid, num_to_kill)):

        users.remove_potion(person.id)
        loot = mon.get_loot(monsterid, int(num_to_kill), factor=items.get_luck_factor(person.id))
        users.update_inventory(person.id, loot)
        out += print_loot(loot, person, monster_name, num_to_kill)

        xp_gained = XP_FACTOR * mon.get_attr(monsterid, key=mon.XP_KEY) * int(num_to_kill)
        cb_level_before = users.xp_to_level(users.read_user(person.id, users.COMBAT_XP_KEY))
        slay_level_before = users.xp_to_level(users.read_user(person.id, users.SLAYER_XP_KEY))
        users.update_user(person.id, xp_gained, users.SLAYER_XP_KEY)
        users.update_user(person.id, round(0.7 * xp_gained), users.COMBAT_XP_KEY)
        cb_level_after = users.xp_to_level(users.read_user(person.id, users.COMBAT_XP_KEY))
        slay_level_after = users.xp_to_level(users.read_user(person.id, users.SLAYER_XP_KEY))

        slayer_xp_formatted = '{:,}'.format(xp_gained)
        combat_xp_formatted = '{:,}'.format(round(0.7 * xp_gained))
        out += f'\nYou have also gained {slayer_xp_formatted} slayer xp and {combat_xp_formatted} combat xp. '
        if cb_level_after > cb_level_before:
            out += f'In addition, you have gained {cb_level_after - cb_level_before} combat levels. '
        if slay_level_after > slay_level_before:
            out += f'Also, as well, you have gained {slay_level_after - slay_level_before} slayer levels. '
    else:
        users.remove_potion(person.id)
        factor = int(chance)/100
        factor *= items.get_luck_factor(person.id)
        loot = mon.get_loot(monsterid, int(num_to_kill), factor=factor)
        users.update_inventory(person.id, loot)
        out += print_loot(loot, person, monster_name, num_to_kill)

        xp_gained = round(XP_FACTOR * mon.get_attr(monsterid, key=mon.XP_KEY) * int(num_to_kill) * factor)
        cb_level_before = users.xp_to_level(users.read_user(person.id, users.COMBAT_XP_KEY))
        slay_level_before = users.xp_to_level(users.read_user(person.id, users.SLAYER_XP_KEY))
        users.update_user(person.id, xp_gained, users.SLAYER_XP_KEY)
        users.update_user(person.id, round(0.7 * xp_gained), users.COMBAT_XP_KEY)
        cb_level_after = users.xp_to_level(users.read_user(person.id, users.COMBAT_XP_KEY))
        slay_level_after = users.xp_to_level(users.read_user(person.id, users.SLAYER_XP_KEY))

        slayer_xp_formatted = '{:,}'.format(xp_gained)
        combat_xp_formatted = '{:,}'.format(round(0.7 * xp_gained))
        out += f'\nYou have received lower loot and experience because you have died.'\
               f'\nYou have received {slayer_xp_formatted} slayer xp and {combat_xp_formatted} combat xp. '
        if cb_level_after > cb_level_before:
            out += f'In addition, you have gained {cb_level_after - cb_level_before} combat levels. '
        if slay_level_after > slay_level_before:
            out += f'Also, as well, you have gained {slay_level_after - slay_level_before} slayer levels. '

    return out


def get_reaper_result(person, *args):
    """Determines the success and loot of a reaper task."""
    try:
        monsterid, monster_name, num_to_kill, chance = args[0]
    except ValueError as e:
        print(e)
        raise ValueError
    out = ''
    users.add_counter(person.id, monsterid, num_to_kill)
    if adv.is_success(calc_chance(person.id, monsterid, num_to_kill)):
        users.remove_potion(person.id)
        factor = 0.7 * items.get_luck_factor(person.id)
        loot = mon.get_loot(monsterid, int(num_to_kill), factor=factor)
        loot['291'] = 1
        users.update_inventory(person.id, loot)
        out += print_loot(loot, person, monster_name, num_to_kill)

        xp_gained = XP_FACTOR * mon.get_attr(monsterid, key=mon.XP_KEY) * int(num_to_kill)
        cb_level_before = users.xp_to_level(users.read_user(person.id, users.COMBAT_XP_KEY))
        slay_level_before = users.xp_to_level(users.read_user(person.id, users.SLAYER_XP_KEY))
        users.update_user(person.id, xp_gained, users.SLAYER_XP_KEY)
        users.update_user(person.id, round(0.7 * xp_gained), users.COMBAT_XP_KEY)
        cb_level_after = users.xp_to_level(users.read_user(person.id, users.COMBAT_XP_KEY))
        slay_level_after = users.xp_to_level(users.read_user(person.id, users.SLAYER_XP_KEY))

        slayer_xp_formatted = '{:,}'.format(xp_gained)
        combat_xp_formatted = '{:,}'.format(round(0.7 * xp_gained))
        out += f'\nYou have also gained {slayer_xp_formatted} slayer xp and {combat_xp_formatted} combat xp. '
        if cb_level_after > cb_level_before:
            out += f'In addition, you have gained {cb_level_after - cb_level_before} combat levels. '
        if slay_level_after > slay_level_before:
            out += f'Also, as well, you have gained {slay_level_after - slay_level_before} slayer levels. '
    else:

        users.remove_potion(person.id)
        factor = int(chance)/170 * items.get_luck_factor(person.id)
        loot = mon.get_loot(monsterid, int(num_to_kill), factor=factor)
        loot.append('291')
        users.update_inventory(person.id, loot)
        out += print_loot(loot, person, monster_name, num_to_kill)

        xp_gained = round(XP_FACTOR * mon.get_attr(monsterid, key=mon.XP_KEY) * int(num_to_kill) * factor)
        cb_level_before = users.xp_to_level(users.read_user(person.id, users.COMBAT_XP_KEY))
        slay_level_before = users.xp_to_level(users.read_user(person.id, users.SLAYER_XP_KEY))
        users.update_user(person.id, xp_gained, users.SLAYER_XP_KEY)
        users.update_user(person.id, round(0.7 * xp_gained), users.COMBAT_XP_KEY)
        cb_level_after = users.xp_to_level(users.read_user(person.id, users.COMBAT_XP_KEY))
        slay_level_after = users.xp_to_level(users.read_user(person.id, users.SLAYER_XP_KEY))

        slayer_xp_formatted = '{:,}'.format(xp_gained)
        combat_xp_formatted = '{:,}'.format(round(0.7 * xp_gained))
        out += f'\nYou have received lower loot and experience because you have died.'\
               f'\nYou have received {slayer_xp_formatted} slayer xp and {combat_xp_formatted} combat xp. '
        if cb_level_after > cb_level_before:
            out += f'In addition, you have gained {cb_level_after - cb_level_before} combat levels. '
        if slay_level_after > slay_level_before:
            out += f'Also, as well, you have gained {slay_level_after - slay_level_before} slayer levels. '
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
        user_level = users.xp_to_level(users.read_user(userid, key=users.COMBAT_XP_KEY))
        completed_quests = set(users.get_completed_quests(userid))
        equipment = users.read_user(userid, key=users.EQUIPMENT_KEY)
        for _ in range(1000):
            monsterid = mon.get_random(slayer_level=users.xp_to_level(users.read_user(userid, key=users.SLAYER_XP_KEY)))
            num_to_kill = mon.get_task_length(monsterid)
            base_time, task_length = calc_length(userid, monsterid, num_to_kill)
            chance = calc_chance(userid, monsterid, num_to_kill)
            mon_level = mon.get_attr(monsterid, key=mon.LEVEL_KEY)
            # print(f'{monsterid} {task_length/base_time} {chance}')
            if 0.25 <= task_length / base_time <= 2 and chance >= 20 and mon_level / user_level >= 0.8\
                    and mon.get_attr(monsterid, key=mon.SLAYER_KEY) is True\
                    and ({mon.get_attr(monsterid, key=mon.QUEST_REQ_KEY)}.issubset(completed_quests)
                    or mon.get_attr(monsterid, key=mon.QUEST_REQ_KEY) == 0):
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
        out = adv.print_adventure(userid)
        out += adv.print_on_adventure_error('task')
    return out


def get_reaper_task(userid):
    """Assigns a user a reaper task provided they are not in the middle of another adventure."""
    out = SLAYER_HEADER
    if users.get_level(userid, key=users.SLAYER_XP_KEY) < 50:
        out += "Your slayer level is too low to start a reaper task. You need at least 50 slayer."
        return out
    print(users.read_user(userid, key=users.LAST_REAPER_KEY))
    if datetime.datetime.fromtimestamp(users.read_user(userid, key=users.LAST_REAPER_KEY)).date() \
            >= datetime.date.today():
        out += 'You have already done a reaper task today. Please come back tomorrow for another one.'
        return out

    if not adv.is_on_adventure(userid):
        completed_quests = set(users.get_completed_quests(userid))
        for _ in range(1000):
            monsterid = mon.get_random(slayer_level=users.xp_to_level(users.read_user(userid, key=users.SLAYER_XP_KEY)))
            num_to_kill = mon.get_task_length(monsterid)
            base_time, task_length = calc_length(userid, monsterid, num_to_kill)
            chance = calc_chance(userid, monsterid, num_to_kill)
            # print(f'{monsterid} {task_length/base_time} {chance}')
            if 0.25 <= task_length / base_time <= 2 and chance >= 20 \
                    and mon.get_attr(monsterid, key=mon.BOSS_KEY) is True\
                    and ({mon.get_attr(monsterid, key=mon.QUEST_REQ_KEY)}.issubset(completed_quests)
                    or mon.get_attr(monsterid, key=mon.QUEST_REQ_KEY) == 0):
                break
        else:
            return "Error: gear too low to fight any monsters. Please equip some better gear and try again. " \
                   "If you are new, type `~starter` to get a bronze kit."
        monster_name = mon.get_attr(monsterid)
        task = adv.format_line(5, userid, adv.get_finish_time(task_length), monsterid,
                               monster_name, num_to_kill, chance)
        adv.write(task)
        users.update_user(userid, datetime.date.today(), key=users.LAST_REAPER_KEY)
        out += print_task(userid, reaper=True)
    else:
        out = adv.print_adventure(userid)
        out += adv.print_on_adventure_error('reaper task')
    return out


def print_loot(loot, person, monster_name, num_to_kill, add_mention=True):
    """Converts a user's loot from a slayer task to a string."""
    out = f'{SLAYER_HEADER}**'
    if add_mention:
        out += f'{person.mention}, '
    else:
        out += f'{person.name}, '
    monsterid = mon.find_by_name(monster_name)
    out += f'Your loot from your {num_to_kill} {mon.add_plural(monsterid)} has arrived!**\n'

    rares = mon.get_rares(monster_name)
    for key in loot.keys():
        if key in rares:
            out += f'**{loot[key]} {items.get_attr(key)}**\n'
        else:
            out += f'{loot[key]} {items.get_attr(key)}\n'

    total_value = '{:,}'.format(users.get_value_of_inventory(loot))
    out += f'*Total value: {total_value}*'

    return out


def print_chance(userid, monsterid, monster_dam=-1, monster_acc=-1, monster_arm=-1, monster_combat=-1, xp=-1, number=100, dragonfire=False):
    equipment = users.read_user(userid, key=users.EQUIPMENT_KEY)
    player_dam, player_acc, player_arm = users.get_equipment_stats(equipment)
    player_combat = users.xp_to_level(users.read_user(userid, key=users.SLAYER_XP_KEY))
    if monster_dam == -1:
        monster_dam = mon.get_attr(monsterid, key=mon.DAMAGE_KEY)
        monster_acc = mon.get_attr(monsterid, key=mon.ACCURACY_KEY)
        monster_arm = mon.get_attr(monsterid, key=mon.ARMOUR_KEY)
        xp = mon.get_attr(monsterid, key=mon.XP_KEY)
        monster_combat = mon.get_attr(monsterid, key=mon.LEVEL_KEY)
    if dragonfire:
        monster_base = 100
    else:
        monster_base = 1

    c = 1 + monster_combat / 200
    d = 1 + player_combat / 99
    dam_multiplier = monster_base + monster_acc / 200
    chance = round(min(100 * max(0, (2 * d * player_arm) / (number / 50 * monster_dam * dam_multiplier + c)), 100))
    # chance = round(min(100 * max(0, (player_arm / (monster_dam * dam_multiplier + 1 + monster_combat / 200)) / 2 + player_combat / 200), 100))

    dam_multiplier = 1 + player_acc / 200
    base_time = math.floor(number * xp / 10)
    time = round(base_time * (monster_arm * monster_base / (player_dam * dam_multiplier + player_combat)))
    out = f'level {monster_combat} monster with {monster_dam} dam {monster_acc} acc {monster_arm} arm giving {xp} xp: '\
          f'chance: {chance}%, base time: {base_time}, time to kill {number}: {time}, time ratio: {time / base_time}.'
    return out


def print_kill_status(time_left, *args):
    monsterid, monster_name, number, length = args[0]
    out = f'{SLAYER_HEADER}' \
          f'You are currently killing {number} {mon.add_plural(monsterid)} for {length} minutes. ' \
          f'You can see your loot {time_left}.'
    return out


def print_status(time_left, *args):
    monsterid, monster_name, num_to_kill, chance = args[0]
    out = f'{SLAYER_HEADER}' \
          f'You are currently slaying {num_to_kill} {mon.add_plural(monsterid)}. ' \
          f'You can see the results of this slayer task {time_left}. ' \
          f'You currently have a {chance}% chance of succeeding with your current gear. '
    return out


def print_reaper_status(time_left, *args):
    monsterid, monster_name, num_to_kill, chance = args[0]
    out = f'{SLAYER_HEADER}' \
          f'You are currently on a reaper task of {num_to_kill} {mon.add_plural(monsterid)}. ' \
          f'You can see the results of this slayer task {time_left}. ' \
          f'You currently have a {chance}% chance of succeeding with your current gear. '
    return out


def print_task(userid, reaper=False):
    """Converts a user's task into a string."""
    taskid, userid, task_length, monsterid, monster_name, num_to_kill, chance = get_task_info(userid)
    if reaper:
        out = f'New reaper task received: '
    else:
        out = f'New slayer task received: '
    out += f'Kill __{num_to_kill} {mon.add_plural(monsterid)}__!\n'
    out += f'This will take {task_length} minutes '
    out += f'and has a success rate of {chance}% with your current gear. '
    return out
