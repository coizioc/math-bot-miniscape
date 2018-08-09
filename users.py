import ujson
from collections import Counter

from subs.miniscape import items
from subs.miniscape.files import USERS_JSON, XP_FILE, ARMOUR_SLOTS_FILE

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

ITEMS_KEY = 'items'             # User's inventory, stored as a Counter.
MONSTERS_KEY = 'monsters'       # Count of monsters user has killed, stored as a Counter.
CLUES_KEY = 'clues'             # Count of clues user has completed, stored as a Counter.
EQUIPMENT_KEY = 'equip'         # User's equipment, stored as a list of size 13 initialized to -1.
COMBAT_XP_KEY = 'combat'        # User's combat xp, stored as an int.
SLAYER_XP_KEY = 'slayer'        # User's slayer xp, stored as an int.
GATHER_XP_KEY = 'gather'        # User's gathering xp, stored as an int.
ARTISAN_XP_KEY = 'artisan'      # User's artisan xp, stored as an int.
POTION_KEY = 'potion'           # User's active potion, stored as an int.
QUESTS_KEY = 'quests'           # User's complted quest. Storted as a hexidecimal number whose bits represent
                                # whether a user has completed a quest with that questid.
DEFAULT_ACCOUNT = {ITEMS_KEY: Counter(),
                   MONSTERS_KEY: Counter(),
                   CLUES_KEY: Counter(),
                   EQUIPMENT_KEY: [-1]*15,
                   COMBAT_XP_KEY: 0,
                   SLAYER_XP_KEY: 0,
                   GATHER_XP_KEY: 0,
                   ARTISAN_XP_KEY: 0,
                   POTION_KEY: 0,
                   QUESTS_KEY: "0x0"}   # What's this?

CHARACTER_HEADER = f'__**:crossed_swords: CHARACTER :crossed_swords:**__\n'


def add_counter(userid, value, number, key=MONSTERS_KEY):
    """Adds a Counter to another Counter in a user's account."""
    new_counts = Counter({value: int(number)})
    with open(USERS_JSON, 'r') as f:
        accounts = ujson.load(f)
    userid = str(userid)
    try:
        monster_kills = Counter(accounts[userid][key])
        monster_kills = monster_kills + new_counts
        accounts[userid][key] = monster_kills
    except KeyError:
        accounts[userid][key] = new_counts
    with open(USERS_JSON, 'w') as f:
        ujson.dump(accounts, f)


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
            slot = items.get_attr(itemid, key=items.SLOT_KEY)
            if slot > 0:
                equipment = read_user(userid, key=EQUIPMENT_KEY)
                if equipment[slot] == -1:
                    equipment[slot] = itemid
                else:
                    update_inventory(userid, [equipment[slot]])
                    equipment[slot] = itemid
                update_inventory(userid, [itemid], remove=True)
                update_user(userid, equipment, EQUIPMENT_KEY)
                return f'{item_name} equipped to {SLOTS[str(slot)]}!'
            else:
                return f'Error: {item_name} cannot be equipped.'
        else:
            return f'Error: {item_name} not in inventory.'
    else:
        return f'Error: Insufficient level to equip item ({item_level}). Your current combat level is {user_cb_level}.'


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
    for item in equipment:
        try:
            damage += items.get_attr(item, key=items.DAMAGE_KEY)
            accuracy += items.get_attr(item, key=items.ACCURACY_KEY)
            armour += items.get_attr(item, key=items.ARMOUR_KEY)
        except KeyError:
            pass
    return damage, accuracy, armour


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
    with open(USERS_JSON, 'r') as f:
        accounts = ujson.load(f)

    userid = str(userid)

    try:
        count = accounts[userid][ITEMS_KEY][item]
        if int(count) >= int(number):
            return True
        else:
            return False
    except KeyError:
        return False


def print_account(userid):
    """Writes a string showing basic user information."""
    combat_xp = read_user(userid, key=COMBAT_XP_KEY)
    slayer_xp = read_user(userid, key=SLAYER_XP_KEY)
    gather_xp = read_user(userid, key=GATHER_XP_KEY)
    artisan_xp = read_user(userid, key=ARTISAN_XP_KEY)
    out = f'{CHARACTER_HEADER}'\
          f'**Combat Level**: {xp_to_level(combat_xp)} *({combat_xp} xp)*\n'\
          f'**Slayer Level**: {xp_to_level(slayer_xp)} *({slayer_xp} xp)*\n' \
          f'**Gathering Level**: {xp_to_level(gather_xp)} *({gather_xp} xp)*\n' \
          f'**Artisan Level**: {xp_to_level(artisan_xp)} *({artisan_xp} xp)*\n\n'

    out += f'**Potion**: '
    potion = read_user(userid, key=POTION_KEY)
    if potion == 0:
        out += 'None\n\n'
    else:
        out += f'{items.get_attr(potion)}\n\n'

    out += print_equipment(userid)

    return out


def print_equipment(userid):
    """Writes a string showing the stats of a user's equipment."""
    out = ''
    equipment = read_user(userid, key=EQUIPMENT_KEY)
    damage, accuracy, armour = get_equipment_stats(equipment)
    out += f'**Damage**: {damage}\n' \
           f'**Accuracy**: {accuracy}\n' \
           f'**Armour**: {armour}\n\n'
    for i in range(1, len(equipment)):
        out += f'**{SLOTS[str(i)].title()}**: '
        if int(equipment[i]) > -1:
            out += f'{items.get_attr(equipment[i])} ' \
                   f'*(dam: {items.get_attr(equipment[i], key=items.DAMAGE_KEY)}, ' \
                   f'acc: {items.get_attr(equipment[i], key=items.ACCURACY_KEY)}, ' \
                   f'arm: {items.get_attr(equipment[i], key=items.ARMOUR_KEY)})*\n'
        else:
            out += f'none *(dam: 0, acc: 0, arm: 0)*\n'
    return out


def print_inventory(person, search):
    """Prints a list of a user's inventory into discord message-sized chunks."""
    inventory = read_user(person.id)
    header = f":moneybag: __**{person.name.upper()}'S INVENTORY**__ :moneybag:\n"
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
    userid = str(userid)
    try:
        with open(USERS_JSON, 'r') as f:
            accounts = ujson.load(f)
        if userid not in accounts:
            accounts[userid] = DEFAULT_ACCOUNT
        if key not in accounts[userid].keys():
            accounts[userid][key] = DEFAULT_ACCOUNT[key]
            with open(USERS_JSON, 'w') as f:
                ujson.dump(accounts, f)
        return accounts[userid][key]
    except KeyError:
        return 0


def update_inventory(userid, loot, remove=False):
    """Adds or removes items from a user's inventory."""
    with open(USERS_JSON, 'r') as f:
        accounts = ujson.load(f)
    try:
        inventory = Counter(accounts[str(userid)]['items'])
        loot = Counter(loot)
        inventory = inventory - loot if remove else inventory + loot
        accounts[str(userid)]['items'] = inventory
    except KeyError:
        if remove:
            raise ValueError
        else:
            accounts[str(userid)] = {}
            accounts[str(userid)]['items'] = Counter(loot)
    with open(USERS_JSON, 'w') as f:
        ujson.dump(accounts, f)


def update_user(userid, value, key=ITEMS_KEY):
    """Changes the value of a key within a user's account."""
    userid = str(userid)
    with open(USERS_JSON, 'r') as f:
        accounts = ujson.load(f)

    if userid not in accounts:
        accounts[userid] = DEFAULT_ACCOUNT
    if key not in accounts[userid].keys():
        accounts[userid][key] = DEFAULT_ACCOUNT[key]
    if key == COMBAT_XP_KEY or key == SLAYER_XP_KEY or key == GATHER_XP_KEY or key == ARTISAN_XP_KEY:
        current_xp = accounts[userid][key]
        accounts[userid][key] = current_xp + value
    elif key == EQUIPMENT_KEY or key == ITEMS_KEY or key == POTION_KEY:
        accounts[userid][key] = value
    elif key == QUESTS_KEY:
        current_quests = int(str(accounts[userid][key])[2:], 16)
        current_quests = current_quests | 1 << (int(value) - 1)
        accounts[userid][key] = str(hex(current_quests))

    with open(USERS_JSON, 'w') as f:
        ujson.dump(accounts, f)


def xp_to_level(xp):
    """Converts a  user's xp into its equivalent level based on an XP table."""
    for level_xp in XP:
        if int(level_xp) > xp:
            return int(XP[level_xp]) - 1
    else:
        return 99
