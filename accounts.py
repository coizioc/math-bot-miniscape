import ujson
import math
from collections import Counter

from subs.miniscape.files import ACCOUNTS_JSON, XP_FILE, ARMOUR_FILE
from subs.miniscape import items

XP = {}
with open(XP_FILE, 'r') as f:
    for line in f.read().splitlines():
        line_split = line.split(';')
        XP[line_split[0]] = line_split[1]

SLOTS = {}
with open(ARMOUR_FILE, 'r') as f:
    for line in f.read().splitlines()[1:]:
        line_split = line.split(';')
        SLOTS[line_split[0]] = line_split[1]

ITEMS_KEY = 'items'
EQUIPMENT_KEY = 'equip'
COMBAT_XP_KEY = 'combat'
SLAYER_XP_KEY = 'slayer'
DEFAULT_ACCOUNT = {ITEMS_KEY: Counter(),
                   EQUIPMENT_KEY: [-1]*13,
                   COMBAT_XP_KEY: 0,
                   SLAYER_XP_KEY: 0}


def update_account(userid, amount, key=ITEMS_KEY):
    """Changes the value of a key within a user's account."""
    userid = str(userid)
    with open(ACCOUNTS_JSON, 'r') as f:
        accounts = ujson.load(f)

    if userid not in accounts:
        accounts[userid] = DEFAULT_ACCOUNT
    if key not in accounts[userid].keys():
        accounts[userid][key] = DEFAULT_ACCOUNT[key]

    accounts[str(userid)][key] = amount

    with open(ACCOUNTS_JSON, 'w') as f:
        ujson.dump(accounts, f)


def read_account(userid, key=ITEMS_KEY):
    """Reads the value of a key within a user's account."""
    userid = str(userid)
    try:
        with open(ACCOUNTS_JSON, 'r') as f:
            accounts = ujson.load(f)
        if userid not in accounts:
            accounts[userid] = DEFAULT_ACCOUNT
        if key not in accounts[userid].keys():
            accounts[userid][key] = DEFAULT_ACCOUNT[key]
            with open(ACCOUNTS_JSON, 'w') as f:
                ujson.dump(accounts, f)
        return accounts[userid][key]
    except KeyError:
        return 0


def xp_to_level(xp):
    for level_xp in XP:
        if int(level_xp) > xp:
            return int(XP[level_xp]) - 1
    else:
        return 99


def xp_to_combat(xp):
    level = xp_to_level(xp)
    return math.floor(7 * level / 5)


def equip_item(userid, item):
    try:
        itemid = items.find_item_by_name(item)
    except KeyError:
        return f'Error: {item} does not exist.'
    item_name = items.get_item_attr(itemid)
    if items.item_in_inventory(userid, itemid):
        slot = items.get_item_attr(itemid, key=items.SLOT_KEY)
        if slot > 0:
            equipment = read_account(userid, key=EQUIPMENT_KEY)
            if equipment[slot] == -1:
                equipment[slot] = itemid
            else:
                add_inventory(userid, [equipment[slot]])
                equipment[slot] = itemid
            remove_inventory(userid, itemid, 1)
            update_account(userid, equipment, EQUIPMENT_KEY)
            return f'{item_name} equipped to {SLOTS[str(slot)]}!'
        else:
            return f'Error: {item_name} cannot be equipped.'
    else:
        return f'Error: {item_name} not in inventory.'


def get_equipment_stats(equipment):
    damage = 0
    accuracy = 0
    armour = 0
    for item in equipment:
        try:
            damage += items.get_item_attr(item, key=items.DAMAGE_KEY)
            accuracy += items.get_item_attr(item, key=items.ACCURACY_KEY)
            armour += items.get_item_attr(item, key=items.ARMOUR_KEY)
        except KeyError:
            pass
    return tuple((damage, accuracy, armour))


def add_inventory(userid, loot):
    with open(ACCOUNTS_JSON, 'r') as f:
        accounts = ujson.load(f)
    try:
        inventory = Counter(accounts[str(userid)]['items'])
        inventory += Counter(loot)
        accounts[str(userid)]['items'] = inventory
    except KeyError:
        accounts[str(userid)] = {}
        accounts[str(userid)]['items'] = loot
    with open(ACCOUNTS_JSON, 'w') as f:
        ujson.dump(accounts, f)


def remove_inventory(userid, itemid, number):
    loot = Counter([itemid] * number)

    with open(ACCOUNTS_JSON, 'r') as f:
        accounts = ujson.load(f)

    try:
        inventory = Counter(accounts[str(userid)]['items'])
        inventory -= loot
        accounts[str(userid)]['items'] = inventory
    except KeyError:
        accounts[str(userid)] = {}
        accounts[str(userid)]['items'] = loot
    with open(ACCOUNTS_JSON, 'w') as f:
        ujson.dump(accounts, f)


def print_equipment(userid):
    out = ''
    equipment = read_account(userid, key=EQUIPMENT_KEY)
    damage, accuracy, armour = get_equipment_stats(equipment)
    out += f'**Damage**: {damage}\n' \
           f'**Accuracy**: {accuracy}\n' \
           f'**Armour**: {armour}\n\n'
    for i in range(1, len(equipment)):
        out += f'**{SLOTS[str(i)].title()}**: '
        if int(equipment[i]) > -1:
            out += f'{items.get_item_attr(equipment[i])} ' \
                   f'*(dam: {items.get_item_attr(equipment[i], key=items.DAMAGE_KEY)}, ' \
                   f'acc: {items.get_item_attr(equipment[i], key=items.ACCURACY_KEY)}, ' \
                   f'arm: {items.get_item_attr(equipment[i], key=items.ARMOUR_KEY)})*\n'
        else:
            out += f'none *(dam: 0, acc: 0, arm: 0)*\n'
    return out


def print_account(userid):
    combat_xp = read_account(userid, key=COMBAT_XP_KEY)
    slayer_xp = read_account(userid, key=SLAYER_XP_KEY)
    out = f'__**:crossed_swords: CHARACTER :crossed_swords:**__\n'\
          f'**Combat Level**: {xp_to_level(combat_xp)} *({combat_xp} xp)*\n'\
          f'**Slayer Level**: {xp_to_level(slayer_xp)} *({slayer_xp} xp)*\n\n'\

    out += print_equipment(userid)

    return out
