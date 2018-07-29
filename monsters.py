from collections import Counter
import ujson
import random

from subs.miniscape import items
from subs.miniscape.files import MONSTERS_JSON, MONSTER_DIRECTORY

with open(MONSTERS_JSON, 'r') as f:
    MONSTERS = ujson.load(f)

NAME_KEY = 'name'               # name of the monster
TASK_MIN_KEY = 'task_min'       # min num. of monsters that can be assigned per task
TASK_MAX_KEY = 'task_max'       # max num. of monsters that can be assigned per task
XP_KEY = 'xp'                   # xp per monster kill
SLAYER_REQ_KEY = 'slayer req'   # slayer requirement to kill monster
LEVEL_KEY = 'level'             # combat level of monster
AFFINITY_KEY = 'aff'            # combat type of monster 0: melee, 1: range, 2: mage
ACCURACY_KEY = 'accuracy'       # accuracy of monster
DAMAGE_KEY = 'damage'           # damage of monster
ARMOUR_KEY = 'armour'           # armour of monster
SLAYER_KEY = 'slayer'           # boolean of whether monster is slayable
DRAGON_KEY = 'dragon'           # boolean of whether monster has dragonfire

DEFAULT_MONSTER = {
    NAME_KEY: 'unknown mosnter',
    TASK_MIN_KEY: 1,
    TASK_MAX_KEY: 1,
    XP_KEY: 0,
    SLAYER_REQ_KEY: 1,
    LEVEL_KEY: 1,
    AFFINITY_KEY: 0,
    ACCURACY_KEY: 1,
    DAMAGE_KEY: 1,
    ARMOUR_KEY: 1,
    SLAYER_KEY: True,
    DRAGON_KEY: False
}

RARITY_NAMES = {
        1: 'always',
        16: 'common',
        128: 'uncommon',
        256: 'rare',
        1024: 'super rare',
        4096: 'ultra rare'
    }


def add_plural(monsterid):
    return get_attr(monsterid) + 's'


def find_by_name(name):
    """Finds a monster's ID from its name."""
    name = name.lower()
    for monsterid in list(MONSTERS.keys()):
        if name == MONSTERS[monsterid][NAME_KEY]:
            return monsterid
    else:
        raise KeyError


def get_attr(monsterid, key=NAME_KEY):
    """Gets the value of a (given) key of a monster given its id."""
    monsterid = str(monsterid)
    if monsterid in set(MONSTERS.keys()):
        try:
            return MONSTERS[monsterid][key]
        except KeyError:
            MONSTERS[monsterid][key] = DEFAULT_MONSTER[key]
            return MONSTERS[monsterid][key]
    else:
        raise KeyError


def get_loot_table(monsterid):
    """Creates and returns a dictionary of possible loot from a monster given its id."""
    loot_table = {}
    with open(f'{MONSTER_DIRECTORY}{str(monsterid)}.txt') as f:
        items = f.read().splitlines()
    for item in items:
        itemid, itemmin, itemmax, rarity = item.split(';')
        loot_table[itemid] = {}
        loot_table[itemid]['min'] = int(itemmin)
        loot_table[itemid]['max'] = int(itemmax)
        loot_table[itemid]['rarity'] = int(rarity)
    return loot_table


def get_loot(monsterid, num_to_kill, factor=1):
    """Generates a Counter from a number of killed monsters given its id."""
    loot_table = get_loot_table(monsterid)
    max_rarity = get_max_rarity(loot_table)
    num_to_kill = int(num_to_kill)
    loot = []
    for key in loot_table.keys():
        if loot_table[key]['rarity'] == 1:
            loot.extend([key] * num_to_kill)
    for _ in range(int(num_to_kill)):
        for _ in range(round(8 * factor)):
            item = random.sample(loot_table.keys(), 1)[0]
            item_chance = loot_table[item]['rarity']
            if random.randint(1, item_chance) == 1 and int(item_chance) > 1:
                item_min = loot_table[item]['min']
                item_max = loot_table[item]['max']
                for _ in range(random.randint(item_min, item_max)):
                    loot.append(item)
    return Counter(loot)


def get_max_rarity(loot_table):
    """Gets the highest rarity value from a dictionary of a monster's possible loot."""
    max_rarity = 0
    for key in loot_table.keys():
        rarity = loot_table[key]['rarity']
        max_rarity = rarity if rarity > max_rarity else max_rarity
    return max_rarity


def get_rares(monster_name):
    monsterid = find_by_name(monster_name)
    loottable = get_loot_table(monsterid)

    rares = []
    for item in list(loottable.keys()):
        if int(loottable[item]['rarity']) >= 1024:
            rares.append(item)
    return rares


def get_task_length(monsterid):
    task_min = MONSTERS[monsterid][TASK_MIN_KEY]
    task_max = MONSTERS[monsterid][TASK_MAX_KEY]

    return random.randint(task_min, task_max)


def get_random(check_for_key=None, slayer_level=1):
    """Randomly selects and returns a monster (given a particular boolean key)."""
    while True:
        monsterid = random.sample(MONSTERS.keys(), 1)[0]
        if slayer_level >= get_attr(monsterid, key=SLAYER_REQ_KEY):
            if check_for_key is not None:
                if MONSTERS[monsterid][check_for_key] is True:
                    return monsterid
            else:
                return monsterid


def print_item_from_lootable(item):
    out = '**Drop Sources**:\n'
    for monsterid in list(MONSTERS.keys()):
        loottable = get_loot_table(monsterid)
        for itemid in list(loottable.keys()):
            if int(itemid) == int(item):
                name = MONSTERS[monsterid][NAME_KEY]
                item_min = int(loottable[itemid]['min'])
                item_max = int(loottable[itemid]['max'])
                rarity = int(loottable[itemid]['rarity'])

                out += f'{MONSTERS[monsterid][NAME_KEY].title()} *(amount: '

                if item_min == item_max:
                    out += f'{item_min}, '
                else:
                    out += f'{item_min}-{item_max}, '

                for key in list(RARITY_NAMES.keys()):
                    if key <= rarity:
                        name = key
                    else:
                        break

                out += f'rarity: {RARITY_NAMES[name]})*\n'
    return out


def print_list():
    """Prints a string containing a list of all monsters."""
    header = '__**:skull_crossbones: BESTIARY :skull_crossbones:**__\n'
    messages = []
    monster_list = []
    for monsterid in list(MONSTERS.keys()):
        level = get_attr(monsterid, key=LEVEL_KEY)
        name = get_attr(monsterid)
        slayer_req = get_attr(monsterid, key=SLAYER_REQ_KEY)
        monster_list.append((level, name, slayer_req))
    out = header
    for level, name, req in sorted(monster_list):
        if len(out) >= 1800:
            messages.append(out)
            out = header
        out += f'**{name.title()}** *(combat: {level}, slayer: {req})*\n'
    messages.append(out)
    return messages


def print_monster(monster):
    """Prints information related to a monster."""
    try:
        monsterid = find_by_name(monster.lower())
    except KeyError:
        return [f'Error: {monster} is not a monster.']

    messages = []

    out = f'__**:skull_crossbones: BESTIARY :skull_crossbones:**__\n'\
          f'**Name**: {MONSTERS[monsterid][NAME_KEY].title()}\n'\
          f'**Level**: {MONSTERS[monsterid][LEVEL_KEY]}\n'\
          f'**Accuracy**: {MONSTERS[monsterid][ACCURACY_KEY]}\n'\
          f'**Damage**: {MONSTERS[monsterid][DAMAGE_KEY]}\n'\
          f'**Armour**: {MONSTERS[monsterid][ARMOUR_KEY]}\n'\
          f'**XP**: {MONSTERS[monsterid][XP_KEY]}\n\n'\
          f'**Loot Table**:\n'

    loottable = get_loot_table(monsterid)

    for item in list(loottable.keys()):
        itemname = items.get_attr(item)
        itemmin = int(loottable[item]['min'])
        itemmax = int(loottable[item]['max'])
        rarity = loottable[item]['rarity']
        for key in list(RARITY_NAMES.keys()):
            if key <= rarity:
                name = key
            else:
                break

        out += f"{itemname} *(amount: "
        if itemmin == itemmax:
            out += f'{itemmin}, '
        else:
            out += f"{itemmin}-{itemmax}, "
        out += f"rarity: {RARITY_NAMES[name]})*\n"

        if len(out) >= 1800:
            messages.append(out)
            out = f'__**:skull_crossbones: BESTIARY :skull_crossbones:**__\n'
    messages.append(out)
    return messages
