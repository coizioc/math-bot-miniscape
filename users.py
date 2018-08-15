import ujson
from collections import Counter
import time
import os
import shutil
import datetime

from subs.miniscape import items
from subs.miniscape import quests
from subs.miniscape.files import USER_DIRECTORY, BACKUP_DIRECTORY, XP_FILE, ARMOUR_SLOTS_FILE

XP = {}
with open(XP_FILE, 'r') as f:
    for line in f.read().splitlines():
        line_split = line.split(';')
        XP[line_split[0]] = line_split[1]

SLOTS = {}
with open(ARMOUR_SLOTS_FILE, 'r') as f:
    for line in f.read().splitlines()[1:]:
        line_split = line.split(';')
        SLOTS[line_split[0]] = line_split[1]

IRONMAN_KEY = 'ironman'         # User's ironman status, stored as a boolean.
ITEMS_KEY = 'items'             # User's inventory, stored as a Counter.
MONSTERS_KEY = 'monsters'       # Count of monsters user has killed, stored as a Counter.
CLUES_KEY = 'clues'             # Count of clues user has completed, stored as a Counter.
EQUIPMENT_KEY = 'equip'         # User's equipment, stored as a dicr.
COMBAT_XP_KEY = 'combat'        # User's combat xp, stored as an int.
SLAYER_XP_KEY = 'slayer'        # User's slayer xp, stored as an int.
GATHER_XP_KEY = 'gather'        # User's gathering xp, stored as an int.
ARTISAN_XP_KEY = 'artisan'      # User's artisan xp, stored as an int.
LAST_REAPER_KEY = 'reaper'      # Date of user's last reaper task, stored as a date object.
POTION_KEY = 'potion'           # User's active potion, stored as an int.
QUESTS_KEY = 'quests'           # User's completed quests. Stored as a hexadecimal number whose bits represent
                                # whether a user has completed a quest with that questid.
DEFAULT_ACCOUNT = {IRONMAN_KEY: False,
                   ITEMS_KEY: Counter(),
                   MONSTERS_KEY: Counter(),
                   CLUES_KEY: Counter(),
                   EQUIPMENT_KEY: dict(zip(range(1, 16), 15*[-1])),
                   COMBAT_XP_KEY: 0,
                   SLAYER_XP_KEY: 0,
                   GATHER_XP_KEY: 0,
                   ARTISAN_XP_KEY: 0,
                   LAST_REAPER_KEY: datetime.date.today() - datetime.timedelta(days=1),
                   QUESTS_KEY: "0x0"}   # What's this?

CHARACTER_HEADER = f'__**:crossed_swords: $NAME :crossed_swords:**__\n'


def add_counter(userid, value, number, key=MONSTERS_KEY):
    """Adds a Counter to another Counter in a user's account."""
    new_counts = Counter({value: int(number)})
    try:
        with open(f'{USER_DIRECTORY}{userid}.json', 'r') as f:
            userjson = ujson.load(f)
        counts = Counter(userjson[key])
        total_counts = counts + new_counts
        userjson[key] = total_counts
    except FileNotFoundError:
        userjson = DEFAULT_ACCOUNT
        userjson[MONSTERS_KEY] = new_counts
    with open(f'{USER_DIRECTORY}{userid}.json', 'w+') as f:
        ujson.dump(userjson, f)


def backup():
    """Backs up the user files."""
    current_time = int(time.time())
    destination = f'{BACKUP_DIRECTORY}{current_time}/'
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    for file in os.listdir(USER_DIRECTORY):
        shutil.copy(f'{USER_DIRECTORY}{file}', destination)


def clear_inventory(userid, under=None):
    """Removes all items (with value) in an account's inventory."""
    if under is not None:
        max_sell = int(under)
    else:
        max_sell = 2147483647
    inventory = read_user(userid, ITEMS_KEY)
    for itemid in list(inventory.keys()):
        value = items.get_attr(itemid, key=items.VALUE_KEY)
        if inventory[itemid] > 0 and 0 < value < max_sell:
            inventory[itemid] = 0
    update_user(userid, inventory, key=ITEMS_KEY)


def equip_item(userid, item):
    """Takes an item out of a user's inventory and places it into their equipment."""
    try:
        itemid = items.find_by_name(item)
    except KeyError:
        return f'Error: {item} does not exist.'
    item_level = items.get_attr(itemid, key=items.LEVEL_KEY)
    user_cb_level = xp_to_level(read_user(userid, key=COMBAT_XP_KEY))

    if user_cb_level >= item_level:
        item_name = items.get_attr(itemid)
        if item_in_inventory(userid, itemid):
            slot = str(items.get_attr(itemid, key=items.SLOT_KEY))
            if int(slot) > 0:
                equipment = read_user(userid, key=EQUIPMENT_KEY)
                if slot not in equipment.keys() or equipment[slot] == -1:
                    equipment[slot] = itemid
                else:
                    update_inventory(userid, [equipment[slot]])
                    equipment[slot] = itemid
                update_inventory(userid, [itemid], remove=True)
                update_user(userid, equipment, EQUIPMENT_KEY)
                return f'{item_name} equipped to {SLOTS[slot]}!'
            else:
                return f'Error: {item_name} cannot be equipped.'
        else:
            return f'Error: {item_name} not in inventory.'
    else:
        return f'Error: Insufficient level to equip item ({item_level}). Your current combat level is {user_cb_level}.'


def unequip_item(userid, item):
    """Takes an item out of a user's equipment and places it into their inventory."""
    try:
        itemid = items.find_by_name(item)
    except KeyError:
        return f'Error: {item} does not exist.'

    item_name = items.get_attr(itemid)
    equipment = read_user(userid, key=EQUIPMENT_KEY)
    if itemid in equipment.values():
        slot = str(items.get_attr(itemid, key=items.SLOT_KEY))
        if int(slot) > 0:
            equipment = read_user(userid, key=EQUIPMENT_KEY)
            if equipment[slot] == -1:
                return f'{item_name} is not equipped in {SLOTS[str(slot)]}.'
            update_inventory(userid, [itemid])
            equipment[slot] = -1
            update_user(userid, equipment, EQUIPMENT_KEY)
            return f'{item_name} unequipped from {SLOTS[str(slot)]}!'
        else:
            return f'Error: {item_name} cannot be unequipped.'
    else:
        return f'You do not have {item_name} equipped.'


def get_coins_in_inventory(userid):
    return
    # TODO finish this method.

def get_completed_quests(userid):
    hex_number = int(str(read_user(userid, key=QUESTS_KEY))[2:], 16)
    binary_number = str(bin(hex_number))[2:]
    completed_quests = []
    for bit in range(len(binary_number)):
        if binary_number[bit] == '1':
            completed_quests.append(len(binary_number) - bit)
    return completed_quests


def get_equipment_stats(equipment):
    """Gets the total combat stats for the current equipment worn by a user."""
    damage = 0
    accuracy = 0
    armour = 0
    for itemid in equipment.values():
        try:
            damage += items.get_attr(itemid, key=items.DAMAGE_KEY)
            accuracy += items.get_attr(itemid, key=items.ACCURACY_KEY)
            armour += items.get_attr(itemid, key=items.ARMOUR_KEY)
        except KeyError:
            pass
    return damage, accuracy, armour


def get_level(userid, key):
    """Gets a user's skill level from their userid."""
    xp = read_user(userid, key=key)
    return xp_to_level(xp)


def get_value_of_inventory(inventory, under=None):
    """Gets the total value of a user's inventory."""
    if under is not None:
        max_value = int(under)
    else:
        max_value = 999999999999
    total_value = 0
    for item in list(inventory.keys()):
        value = items.get_attr(item, key=items.VALUE_KEY)
        if value < max_value:
            total_value += int(inventory[item]) * value
    return total_value


def item_in_inventory(userid, item, number=1):
    """Determines whether (a given number of) an item is in a user's inventory."""
    with open(f'{USER_DIRECTORY}{userid}.json', 'r+') as f:
        userjson = ujson.load(f)

    try:
        count = userjson[ITEMS_KEY][item]
        if int(count) >= int(number):
            return True
        else:
            return False
    except KeyError:
        return False


def parse_int(number_as_string):
    """Converts an string into an int if the string represents a valid integer"""
    try:
        if len(number_as_string) > 1:
            int(str(number_as_string)[:-1])
        else:
            if len(number_as_string) == 0:
                raise ValueError
            if len(number_as_string) == 1 and number_as_string.isdigit():
                return int(number_as_string)
            else:
                raise ValueError
    except ValueError:
        raise ValueError
    last_char = str(number_as_string)[-1]
    if last_char.isdigit():
        return int(number_as_string)
    elif last_char == 'k':
        return int(number_as_string[:-1]) * 1000
    elif last_char == 'm':
        return int(number_as_string[:-1]) * 1000000
    elif last_char == 'b':
        return int(number_as_string[:-1]) * 1000000000
    else:
        raise ValueError


def print_account(userid, nickname, printequipment=True):
    """Writes a string showing basic user information."""
    combat_xp = read_user(userid, key=COMBAT_XP_KEY)
    slayer_xp = read_user(userid, key=SLAYER_XP_KEY)
    gather_xp = read_user(userid, key=GATHER_XP_KEY)
    artisan_xp = read_user(userid, key=ARTISAN_XP_KEY)
    combat_level = xp_to_level(combat_xp)
    slayer_level = xp_to_level(slayer_xp)
    gather_level = xp_to_level(gather_xp)
    artisan_level = xp_to_level(artisan_xp)
    total = combat_level + slayer_level + gather_level + artisan_level
    out = f"{CHARACTER_HEADER.replace('$NAME', nickname.upper())}"\
          f'**Combat Level**: {combat_level} *({combat_xp} xp)*\n'\
          f'**Slayer Level**: {slayer_level} *({slayer_xp} xp)*\n' \
          f'**Gathering Level**: {gather_level} *({gather_xp} xp)*\n' \
          f'**Artisan Level**: {artisan_level} *({artisan_xp} xp)*\n'\
          f'**Skill Total**: {total}/{4 * 99}\n\n'\
          f'**Quests Completed**: {len(get_completed_quests(userid))}/{len(quests.QUESTS.keys())}\n\n'

    if printequipment:
        out += print_equipment(userid)

    return out


def print_equipment(userid, name=None, with_header=False):
    """Writes a string showing the stats of a user's equipment."""
    if with_header and name is not None:
        out = f"{CHARACTER_HEADER.replace('$NAME', name.upper())}"
    else:
        out = ''
    equipment = read_user(userid, key=EQUIPMENT_KEY)
    damage, accuracy, armour = get_equipment_stats(equipment)
    out += f'**Damage**: {damage}\n' \
           f'**Accuracy**: {accuracy}\n' \
           f'**Armour**: {armour}\n\n'
    for slot in equipment.keys():
        out += f'**{SLOTS[str(slot)].title()}**: '
        if int(equipment[slot]) > -1:
            out += f'{items.get_attr(equipment[slot])} ' \
                   f'*(dam: {items.get_attr(equipment[slot], key=items.DAMAGE_KEY)}, ' \
                   f'acc: {items.get_attr(equipment[slot], key=items.ACCURACY_KEY)}, ' \
                   f'arm: {items.get_attr(equipment[slot], key=items.ARMOUR_KEY)})*\n'
        else:
            out += f'none *(dam: 0, acc: 0, arm: 0)*\n'
    return out


def print_inventory(person, search):
    """Prints a list of a user's inventory into discord message-sized chunks."""
    inventory = read_user(person.id)
    if person.nick is None:
        name = person.name
    else:
        name = person.nick
    header = f":moneybag: __**{name.upper()}'S INVENTORY**__ :moneybag:\n"
    messages = []
    out = header
    for itemid in list(inventory.keys()):
        name = items.get_attr(itemid)
        if search != '':
            if search not in name.lower():
                continue
        value = items.get_attr(itemid, key=items.VALUE_KEY)
        value_formatted = '{:,}'.format(value)
        item_total_value = int(inventory[itemid]) * value
        item_total_value_formatted = '{:,}'.format(item_total_value)
        if inventory[itemid] > 0:
            out += f'**{items.get_attr(itemid).title()}**: {inventory[itemid]}. ' \
                   f'*(value: {item_total_value_formatted}, {value_formatted} ea.)*\n'
        if len(out) > 1800:
            messages.append(out)
            out = header
    total_value = '{:,}'.format(get_value_of_inventory(inventory))
    out += f'*Total value: {total_value}*\n'
    messages.append(out)
    return messages


def read_user(userid, key=ITEMS_KEY):
    """Reads the value of a key within a user's account."""
    try:
        with open(f'{USER_DIRECTORY}{userid}.json', 'r') as f:
            userjson = ujson.load(f)
        return userjson[key]
    except FileNotFoundError:
        userjson = DEFAULT_ACCOUNT
        with open(f'{USER_DIRECTORY}{userid}.json', 'w+') as f:
            ujson.dump(userjson, f)
        return userjson[key]
    except KeyError:
        userjson[key] = DEFAULT_ACCOUNT[key]
        with open(f'{USER_DIRECTORY}{userid}.json', 'w+') as f:
            ujson.dump(userjson, f)
        return userjson[key]


def remove_potion(userid):
    """Removes a potion from a player's equipment."""
    equipment = read_user(userid, key=EQUIPMENT_KEY)
    equipment['15'] = -1
    update_user(userid, equipment, key=EQUIPMENT_KEY)


def reset_account(userid):
    """Sets a user's keys to the DEFAULT_ACCOUNT."""
    userjson = DEFAULT_ACCOUNT
    with open(f'{USER_DIRECTORY}{userid}.json', 'w+') as f:
        ujson.dump(userjson, f)


def update_inventory(userid, loot, remove=False):
    """Adds or removes items from a user's inventory."""
    try:
        with open(f'{USER_DIRECTORY}{userid}.json', 'r') as f:
            userjson = ujson.load(f)
        inventory = Counter(userjson[ITEMS_KEY])
        loot = Counter(loot)
        inventory = inventory - loot if remove else inventory + loot
        userjson[ITEMS_KEY] = inventory
    except KeyError:
        raise ValueError
    except FileNotFoundError:
        userjson = DEFAULT_ACCOUNT
        userjson[ITEMS_KEY] = Counter(loot)

    with open(f'{USER_DIRECTORY}{userid}.json', 'w+') as f:
        ujson.dump(userjson, f)


def update_user(userid, value, key=ITEMS_KEY):
    """Changes the value of a key within a user's account."""
    userid = str(userid)
    try:
        with open(f'{USER_DIRECTORY}{userid}.json', 'r') as f:
            userjson = ujson.load(f)
    except FileNotFoundError:
        userjson = DEFAULT_ACCOUNT

    if key == COMBAT_XP_KEY or key == SLAYER_XP_KEY or key == GATHER_XP_KEY or key == ARTISAN_XP_KEY:
        current_xp = userjson[key]
        userjson[key] = current_xp + value
    elif key == QUESTS_KEY:
        current_quests = int(str(userjson[key])[2:], 16)
        current_quests = current_quests | 1 << (int(value) - 1)
        userjson[key] = str(hex(current_quests))
    else:
        userjson[key] = value

    with open(f'{USER_DIRECTORY}{userid}.json', 'w+') as f:
        ujson.dump(userjson, f)


def xp_to_level(xp):
    """Converts a  user's xp into its equivalent level based on an XP table."""
    for level_xp in XP:
        if int(level_xp) > xp:
            return int(XP[level_xp]) - 1
    else:
        return 99
