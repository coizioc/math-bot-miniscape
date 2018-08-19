from collections import Counter
import math
import random

from subs.miniscape.files import CLUES_DIRECTORY
from subs.miniscape import users
from subs.miniscape import quests
from subs.miniscape import adventures as adv
from subs.miniscape import items
from subs.miniscape import monsters as mon

DIFFICULTY = {
    1: 'easy',
    2: 'medium',
    3: 'hard',
    4: 'elite',
    5: 'master'
}

CLUE_HEADER = f':map: __**CLUE SCROLL**__ :map:\n'

EASY_CLUE_SCROLL_ID = 184
ROLLS_PER_CLUE = 5


def calc_length(userid, difficulty):
    """Calculates the time it takes to do a clue scroll."""
    quests_completed = len(users.get_completed_quests(userid))
    num_of_quests = len(list(quests.QUESTS.keys()))
    player_damage = users.get_equipment_stats(users.read_user(userid, key=users.EQUIPMENT_KEY))[0] + 1

    quest_multiplier = min((6 - difficulty) * quests_completed / num_of_quests, 1)

    base_time = 450 * difficulty

    time = base_time / (quest_multiplier * player_damage / 200)

    if time/base_time < 0.8:
        time = 0.8 * base_time
    return round(time)


def get_clue_scroll(person, *args):
    try:
        difficulty, length = args[0]
    except ValueError as e:
        print(e)
        raise ValueError
    difficulty = int(difficulty)
    loot = get_loot(difficulty)
    users.update_inventory(person.id, loot)
    users.add_counter(person.id, str(difficulty), 1, key=users.CLUES_KEY)
    out = f'{CLUE_HEADER}' \
          f'{person.mention}, you have finished your {DIFFICULTY[int(difficulty)]} clue scroll! ' \
          f'You have received the following items:\n'
    out += print_loot(loot, difficulty)
    return out


def get_loot(difficulty, factor=1):
    """Generates a Counter of loot from a given clue scroll difficulty."""
    loot_table = get_loot_table(difficulty)
    loot = []
    for _ in range(ROLLS_PER_CLUE):
        for _ in range(round(5 * factor)):
            item = random.sample(loot_table.keys(), 1)[0]
            item_chance = loot_table[item]['rarity']
            if random.randint(1, item_chance) == 1 and int(item_chance) > 1:
                item_min = loot_table[item]['min']
                item_max = loot_table[item]['max']
                for _ in range(random.randint(item_min, item_max)):
                    loot.append(item)
    return Counter(loot)


def get_loot_table(difficulty):
    """Creates and returns a dictionary of possible loot from a clue scroll."""
    loot_table = {}
    with open(f'{CLUES_DIRECTORY}{str(difficulty)}.txt') as f:
        items = f.read().splitlines()
    for item in items:
        itemid, itemmin, itemmax, rarity = item.split(';')
        loot_table[itemid] = {}
        loot_table[itemid]['min'] = int(itemmin)
        loot_table[itemid]['max'] = int(itemmax)
        loot_table[itemid]['rarity'] = int(rarity)
    return loot_table


def get_rares(difficulty):
    loottable = get_loot_table(difficulty)

    rares = []
    for item in list(loottable.keys()):
        if int(loottable[item]['rarity']) > 256:
            rares.append(item)
    return rares


def print_clue_scrolls(userid):
    """Prints the number of clues a user has completed."""
    clue_counts = users.read_user(userid, key=users.CLUES_KEY)

    out = f'{CLUE_HEADER}'
    for difficulty in sorted(list(clue_counts.keys())):
        if clue_counts[difficulty] > 0:
            out += f'**{DIFFICULTY[int(difficulty)].title()}**: {clue_counts[difficulty]}\n'

    return out


def print_item_from_lootable(item):
    out = ''
    for difficulty in range(1, 6):
        loottable = get_loot_table(difficulty)
        for itemid in list(loottable.keys()):
            if int(itemid) == int(item):
                name = f'{DIFFICULTY[difficulty]} clue scroll'
                item_min = int(loottable[itemid]['min'])
                item_max = int(loottable[itemid]['max'])
                rarity = int(loottable[itemid]['rarity'])

                out += f'{name.title()} *(amount: '

                if item_min == item_max:
                    out += f'{item_min}, '
                else:
                    out += f'{item_min}-{item_max}, '

                for key in list(mon.RARITY_NAMES.keys()):
                    if key <= rarity:
                        name = key
                    else:
                        break

                out += f'rarity: {mon.RARITY_NAMES[name]})*\n'
    return out


def print_loot(loot, difficulty):
    """Converts a user's loot from a clue scroll to a string."""
    out = ''
    rares = get_rares(difficulty)
    for key in loot.keys():
        if key in rares:
            out += f'**{loot[key]} {items.get_attr(key)}**\n'
        else:
            out += f'{loot[key]} {items.get_attr(key)}\n'

    total_value = '{:,}'.format(users.get_value_of_inventory(1234567890, inventory=loot))
    out += f'*Total value: {total_value}*'

    return out


def print_status(time_left, *args):
    """Prints a clue scroll and how long until it is finished."""
    difficulty, length = args[0]
    out = f'{CLUE_HEADER}' \
          f'You are currently doing a {DIFFICULTY[int(difficulty)]} clue scroll for {length} minutes. ' \
          f'You will finish {time_left}. '
    return out


def start_clue(userid, difficulty):
    """Starts a clue scroll."""
    out = f'{CLUE_HEADER}'
    if not adv.is_on_adventure(userid):
        scrollid = str(EASY_CLUE_SCROLL_ID + difficulty - 1)
        if not users.item_in_inventory(userid, scrollid):
            return f'Error: you do not have a {DIFFICULTY[difficulty]} clue scroll in your inventory.'
        users.update_inventory(userid, [scrollid], remove=True)

        length = math.floor(calc_length(userid, difficulty) / 60)
        clue = adv.format_line(4, userid, adv.get_finish_time(length * 60), difficulty, length)
        adv.write(clue)
        out += f'You are now doing a {DIFFICULTY[difficulty]} clue scroll for {length} minutes.'
    else:
        out = adv.print_adventure(userid)
        out += adv.print_on_adventure_error('clue scroll')
    return out
