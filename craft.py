import math
import ujson
from collections import Counter

from subs.miniscape import adventures as adv
from subs.miniscape import items
from subs.miniscape import users
from subs.miniscape.files import RECIPE_JSON, XP_FACTOR

GATHER_HEADER = f':hammer_pick: __**GATHERING**__ :hammer_pick: \n'
CRAFT_HEADER = f':hammer_pick: __**CRAFTING**__ :hammer_pick: \n'

with open(RECIPE_JSON, 'r') as f:
    RECIPES = ujson.load(f)

LEVEL_REQ_KEY = 'level req'
QUEST_REQ_KEY = 'quest req'
INPUTS_KEY = 'inputs'
DEFAULT_RECIPE = {
    LEVEL_REQ_KEY: 1,
    QUEST_REQ_KEY: [],
    INPUTS_KEY: Counter()
}


def craft(userid, recipe, n=1):
    """Crafts (a given number of) an item."""
    try:
        recipeid = find_by_name(recipe)
    except KeyError:
        return f'Error: cannot find recipe that crafts {recipe}.'

    name = items.get_attr(recipeid)
    artisan_level = users.xp_to_level(users.read_user(userid, key=users.ARTISAN_XP_KEY))
    artisan_req = get_attr(recipeid, key=LEVEL_REQ_KEY)
    if artisan_level < artisan_req:
        return f'Error: {name} has a artisan requirement ({artisan_req}) ' \
               f'higher than your artisan level ({artisan_level}).'

    inputs = get_attr(recipeid)
    loot = []
    for itemid in list(inputs.keys()):
        if users.item_in_inventory(userid, itemid, number=n * inputs[itemid]):
            loot.extend((n * inputs[itemid]) * [itemid])
        else:
            return f'Error: you do not have enough items to make {n} {items.add_plural(recipeid)} ' \
                   f'({n * inputs[itemid]} {items.add_plural(itemid)}).'

    users.update_inventory(userid, loot, remove=True)
    users.update_inventory(userid, n * [recipeid])
    xp = XP_FACTOR * n * items.get_attr(recipeid, key=items.XP_KEY)
    users.update_user(userid, xp, key=users.ARTISAN_XP_KEY)
    level_after = users.xp_to_level(users.read_user(userid, users.ARTISAN_XP_KEY))

    xp_formatted = '{:,}'.format(xp)
    out = f'Successfully crafted {n} {items.add_plural(recipeid)}! You have also gained {xp_formatted} artisan xp! '
    if level_after > artisan_level:
        out += f'You have also gained {level_after - artisan_level} artisan levels!'
    return out


def calc_length(userid, itemid, number):
    """Calculates the length of gathering a number of an item."""
    gather_level = users.xp_to_level(users.read_user(userid, key=users.GATHER_XP_KEY))
    item_xp = items.get_attr(itemid, key=items.XP_KEY)
    item_level = items.get_attr(itemid, key=items.LEVEL_KEY)
    equipment = users.read_user(userid, key=users.EQUIPMENT_KEY)
    if items.get_attr(itemid, key=items.TREE_KEY):
        if int(equipment[13]) > -1:
            item_multiplier = 2 - (items.get_attr(equipment[13], key=items.LEVEL_KEY) / 100)
        else:
            item_multiplier = 10
    elif items.get_attr(itemid, key=items.TREE_KEY):
        if int(equipment[14]) > -1:
            item_multiplier = 2 - (items.get_attr(equipment[14], key=items.LEVEL_KEY) / 100)
        else:
            item_multiplier = 10
    else:
        item_multiplier = 2

    time_multiplier = gather_level / item_level
    base_time = math.floor(number * item_xp * (100 - item_level) / 200)
    time = round(item_multiplier * base_time / time_multiplier)
    return base_time, time


def calc_number(userid, itemid, time):
    """Calculates the number of items that can be gathered in a given time period."""
    gather_level = users.xp_to_level(users.read_user(userid, key=users.GATHER_XP_KEY))
    item_xp = items.get_attr(itemid, key=items.XP_KEY)
    item_level = items.get_attr(itemid, key=items.LEVEL_KEY)
    equipment = users.read_user(userid, key=users.EQUIPMENT_KEY)
    if items.TREE_KEY:
        if int(equipment[13]) > -1:
            item_multiplier = 2 - (items.get_attr(equipment[13], key=items.LEVEL_KEY) / 100)
        else:
            item_multiplier = 10
    elif items.ROCK_KEY:
        if int(equipment[14]) > -1:
            item_multiplier = 2 - (items.get_attr(equipment[14], key=items.LEVEL_KEY) / 100)
        else:
            item_multiplier = 10
    else:
        item_multiplier = 2
    time_multiplier = gather_level / item_level
    number = math.floor(time * time_multiplier / (item_xp * item_multiplier * ((100 - item_level) / 200)))
    return number


def find_by_name(name):
    """Finds an Recipe's ID from its name."""
    for itemid in list(RECIPES.keys()):
        if name in items.get_attr(itemid):
            return itemid
    else:
        raise KeyError


def get_attr(recipeid, key=INPUTS_KEY):
    """Gets an recipe's attribute from its id."""
    recipeid = str(recipeid)
    if recipeid in set(RECIPES.keys()):
        try:
            return RECIPES[recipeid][key]
        except KeyError:
            RECIPES[recipeid][key] = DEFAULT_RECIPE[key]
            return RECIPES[recipeid][key]
    else:
        raise KeyError


def get_gather(person, *args):
    try:
        itemid, item_name, number, length = args[0]
    except ValueError as e:
        print(e)
        raise ValueError
    loot = int(number) * [itemid]
    xp = XP_FACTOR * int(number) * items.get_attr(itemid, key=items.XP_KEY)
    users.update_inventory(person.id, loot)
    gather_level_before = users.xp_to_level(users.read_user(person.id, users.GATHER_XP_KEY))
    users.update_user(person.id, xp, key=users.GATHER_XP_KEY)
    gather_level_after = users.xp_to_level(users.read_user(person.id, users.GATHER_XP_KEY))

    xp_formatted = '{:,}'.format(xp)
    out = f'{GATHER_HEADER}' \
          f'{person.mention}, your gathering session has finished! You have gathered ' \
          f'{number} {items.add_plural(itemid)} and have gained {xp_formatted} gathering xp! '
    if gather_level_after > gather_level_before:
        out += f'In addition, you have gained {gather_level_after - gather_level_before} gathering levels!'
    users.remove_potion(person.id)
    return out


def print_list(userid):
    """Prints a list of the recipes a user can use."""
    completed_quests = set(users.get_completed_quests(userid))
    messages = []
    out = f'{CRAFT_HEADER}'
    recipe_list = []
    for itemid in list(RECIPES.keys()):
        name = items.get_attr(itemid)
        level = get_attr(itemid, key=LEVEL_REQ_KEY)
        recipe_list.append((level, name))
    for recipe in sorted(recipe_list):
        out += f'**{recipe[1].title()}** *(level {recipe[0]})*\n'
        if len(out) > 1800:
            messages.append(out)
            out = f'{CRAFT_HEADER}'
    out += 'Type `~recipes info [item]` to get more info about how to craft a particular item.'
    messages.append(out)
    return messages


def print_recipe(userid, recipe):
    """Prints details related to a particular recipe."""
    try:
        recipeid = find_by_name(recipe)
    except KeyError:
        return f'Error: cannot find recipe that crafts {recipe}.'

    out = f'{CRAFT_HEADER}'\
          f'**Name**: {items.get_attr(recipeid).title()}\n'\
          f'**Artisan Requirement**: {get_attr(recipeid, key=LEVEL_REQ_KEY)}\n\n'\
          f'**Inputs**:\n'
    inputs = get_attr(recipeid, key=INPUTS_KEY)
    for inputid in list(inputs.keys()):
        if users.item_in_inventory(userid, inputid, inputs[inputid]):
            out += f'~~{inputs[inputid]} {items.add_plural(inputid)}~~\n'
        else:
            out += f'{inputs[inputid]} {items.add_plural(inputid)}\n'

    return out


def print_status(time_left, *args):
    """Prints a gathering and how long until it is finished."""
    itemid, item_name, number, length = args[0]
    out = f'{GATHER_HEADER}' \
          f'You are currently gathering {number} {items.add_plural(itemid)} for {length} minutes. ' \
          f'You will finish {time_left}. '
    return out


def start_gather(userid, item, length=-1, number=-1):
    """Starts a gathering session."""
    out = ''
    if not adv.is_on_adventure(userid):
        try:
            itemid = items.find_by_name(item)
            length = int(length)
            number = int(number)
        except KeyError:
            return f'Error: {item} is not an item.'
        except ValueError:
            return f'Error: {length} is not a valid length of time.'

        if not items.get_attr(itemid, key=items.GATHER_KEY):
            return f'Error: you cannot gather item {items.get_attr(itemid)}.'

        item_name = items.get_attr(itemid)
        gather_level = users.xp_to_level(users.read_user(userid, key=users.GATHER_XP_KEY))
        gather_requirement = items.get_attr(itemid, key=items.LEVEL_KEY)
        player_potion = users.read_user(userid, key=users.EQUIPMENT_KEY)['15']
        if player_potion == '435':
            gather_level = gather_level + 3
        if player_potion == '436':
            gather_level = gather_level + 6

        if gather_level < gather_requirement:
            return f'Error: {item_name} has a gathering requirement ({gather_requirement}) higher ' \
                   f'than your gathering level ({gather_level})'
        quest_req = items.get_attr(itemid, key=items.QUEST_KEY)
        if quest_req not in set(users.get_completed_quests(userid)) and quest_req > 0:
            return f'Error: You do not have the required quest to gather this item.'

        if number > 500:
            number = 500
        if length > 180:
            length = 180

        if int(number) < 0:
            number = calc_number(userid, itemid, length * 60)
            if number > 500:
                number = 500
        elif int(length) < 0:
            length = math.floor(calc_length(userid, itemid, number)[1] / 60)
        else:
            return 'Error: argument missing (number or kill length).'
        gather = adv.format_line(3, userid, adv.get_finish_time(length * 60), itemid, item_name, number, length)
        adv.write(gather)
        out += f'You are now gathering {number} {items.add_plural(itemid)} for {length} minutes.'
    else:
        out = adv.print_adventure(userid)
        out += adv.print_on_adventure_error('gathering')
    return out
