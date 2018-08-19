import math
import ujson
from collections import Counter

from subs.miniscape import adventures as adv
from subs.miniscape import items
from subs.miniscape import users
from subs.miniscape.files import QUESTS_JSON

with open(QUESTS_JSON, 'r') as f:
    QUESTS = ujson.load(f)

NAME_KEY = 'name'
DESCRIPTION_KEY = 'description'
SUCCESS_KEY = 'success'
FAILURE_KEY = 'failure'
ITEM_REQ_KEY = 'item req'
QUEST_REQ_KEY = 'quest req'
REWARD_KEY = 'reward'
DAMAGE_KEY = 'damage'
ACCURACY_KEY = 'accuracy'
ARMOUR_KEY = 'armour'
LEVEL_KEY = 'level'
DRAGON_KEY = 'dragon'
TIME_KEY = 'time'

DEFAULT_QUEST = {
    NAME_KEY: 'Untitled Quest',
    DESCRIPTION_KEY: 'Go something for this person and get some stuff in return.',
    SUCCESS_KEY: 'You did it!',
    FAILURE_KEY: "You didn't do it!",
    ITEM_REQ_KEY: Counter(),
    QUEST_REQ_KEY: [],
    REWARD_KEY: Counter(),
    DAMAGE_KEY: 1,
    ACCURACY_KEY: 1,
    ARMOUR_KEY: 1,
    LEVEL_KEY: 1,
    DRAGON_KEY: False,
    TIME_KEY: 10
}

QUEST_HEADER = ':crossed_swords: __**QUESTS**__ :shield:\n'


def calc_chance(userid, questid):
    """Calculates the chance of success of a quest."""
    equipment = users.read_user(userid, key=users.EQUIPMENT_KEY)
    player_arm = users.get_equipment_stats(equipment)[2]
    monster_acc = get_attr(questid, key=ACCURACY_KEY)
    monster_dam = get_attr(questid, key=DAMAGE_KEY)
    monster_combat = get_attr(questid, key=LEVEL_KEY)
    player_combat = users.xp_to_level(users.read_user(userid, key=users.SLAYER_XP_KEY))
    if get_attr(questid, key=DRAGON_KEY):
        if equipment['7'] == '266' or equipment['7'] == '293':
            monster_base = 1
        else:
            monster_base = 100
    else:
        monster_base = 1

    c = 1 + monster_combat / 200
    d = player_combat / 200
    dam_multiplier = monster_base + monster_acc / 200

    chance = round(min(100 * max(0, (player_arm / (monster_dam * dam_multiplier + c)) / 2 + d), 100))
    return chance


def calc_length(userid, questid):
    """Calculates the length of success of a quest."""
    combat_level = users.xp_to_level(users.read_user(userid, key=users.COMBAT_XP_KEY))
    equipment = users.read_user(userid, key=users.EQUIPMENT_KEY)
    player_dam, player_acc, player_arm = users.get_equipment_stats(equipment)
    monster_arm = get_attr(questid, key=ARMOUR_KEY)
    base_time = 60 * get_attr(questid, key=TIME_KEY)
    if get_attr(questid, key=DRAGON_KEY) and '266' not in equipment:
        monster_base = 100
    else:
        monster_base = 1

    c = combat_level
    dam_multiplier = 1 + player_acc / 200
    time = round(base_time * (monster_arm * monster_base / (player_dam * dam_multiplier + c)))
    if time < 0.5 * base_time:
        time = round(0.5 * base_time)
    if time > 2 * base_time:
        time = 2 * base_time
    return time


def has_item_reqs(userid, questid):
    """Checks if a user can do a quest based on based on whether they have the required items in their inventory."""
    item_reqs = get_attr(questid, key=ITEM_REQ_KEY)
    count = 0
    for itemid in item_reqs:
        if users.item_in_inventory(userid, itemid, item_reqs[itemid]):
            count += 1
    return count == len(item_reqs)


def has_quest_reqs(userid, questid):
    """Checks if a user can do a quest based on based on previous quest requirements."""
    quest_reqs = set(get_attr(questid, key=QUEST_REQ_KEY))
    user_quests = set(users.get_completed_quests(userid))
    return quest_reqs.issubset(user_quests)


def get_attr(questid, key=NAME_KEY):
    """Gets a quest's attribute from its id."""
    questid = str(questid)
    if questid in set(QUESTS.keys()):
        try:
            return QUESTS[questid][key]
        except KeyError:
            QUESTS[questid][key] = DEFAULT_QUEST[key]
            return QUESTS[questid][key]
    else:
        raise KeyError


def get_result(person, *args):
    """Gets the result of a quest."""
    try:
        questid, chance = args[0]
    except ValueError as e:
        print(e)
        raise ValueError

    out = f'{QUEST_HEADER}**{person.mention}, here is the result of your quest, {get_attr(questid)}**:\n'
    if adv.is_success(calc_chance(person.id, questid)):
        out += f'*{get_attr(questid, key=SUCCESS_KEY)}*\n\n'
        reward = get_attr(questid, key=REWARD_KEY)
        out += f'**Reward**:\n'
        loot = []
        for itemid in reward:
            loot.extend(reward[itemid] * [itemid])
            out += f'{reward[itemid]} {items.get_attr(itemid)}\n'
        users.update_inventory(person.id, loot)
        users.update_user(person.id, questid, key=users.QUESTS_KEY)
    else:
        out += f'*{get_attr(questid, key=FAILURE_KEY)}*'
    return out


def print_details(userid, questid):
    """Prints the details of a quest."""
    try:
        name = get_attr(questid)
    except KeyError:
        return f'Error: There is no quest with number {questid}.'

    out = f'{QUEST_HEADER}'

    out += f'**{questid}: {name}**\n'
    out += f'*{get_attr(questid, key=DESCRIPTION_KEY)}*\n\n'

    out += f'**Base Time**: {get_attr(questid, key=TIME_KEY)} minutes.\n'

    if int(questid) in users.get_completed_quests(userid):
        out += f'\n*{get_attr(questid, key=SUCCESS_KEY)}*\n'

    quest_reqs = get_attr(questid, key=QUEST_REQ_KEY)
    if len(quest_reqs) > 0:
        user_quests = set(users.get_completed_quests(userid))
        out += f'\n**Quest Requirements**:\n'
        for quest_req in quest_reqs:
            if quest_req in user_quests:
                out += f'~~{quest_req}. {get_attr(quest_req)}~~\n'
            else:
                out += f'{quest_req}. {get_attr(quest_req)}\n'

    item_reqs = get_attr(questid, key=ITEM_REQ_KEY)
    if len(item_reqs) > 0:
        out += f'\n**Item Requirements**:\n'
        for itemid in item_reqs:
            if users.item_in_inventory(userid, itemid, item_reqs[itemid]):
                out += f'~~{items.add_plural(item_reqs[itemid], itemid)}~~\n'
            else:
                out += f'{items.add_plural(item_reqs[itemid], itemid)}\n'

    out += f'\nIf you would like to do this quest, type `~quest start {questid}`.'
    return out


def print_list(userid):
    """Lists quests a user can do at the moment."""
    out = f'{QUEST_HEADER}'
    messages = []
    for questid in list(QUESTS.keys()):
        if has_quest_reqs(userid, questid):
            if int(questid) in set(users.get_completed_quests(userid)):
                out += f'~~**{questid}**. {get_attr(questid)}~~\n'
            else:
                out += f'**{questid}**. {get_attr(questid)}\n'
            if len(out) > 1800:
                messages.append(out)
                out = f'{QUEST_HEADER}'
    out += f'\n**Quests Completed**: {len(users.get_completed_quests(userid))}/{len(QUESTS.keys())}\n'
    out += 'Type `~quest [quest number]` to see more information about a quest.'
    messages.append(out)
    return messages


def print_quest(questid, time, chance):
    """Prints the quest information into a string."""
    out = f"You are now doing the quest {get_attr(questid)}. This will take {math.floor(time / 60)} minutes " \
          f"and has a {chance}% chance of succeeding with your current gear. "
    return out


def print_status(time_left, *args):
    questid, chance = args[0]
    out = f'{QUEST_HEADER}' \
          f'You are already on the quest {get_attr(questid)}. You can see the results of this quest {time_left}. ' \
          f'You currently have a {chance}% of succeeding with your current gear. '
    return out


def start_quest(userid, questid):
    """Assigns a user a slayer task provided they are not in the middle of another adventure."""
    out = QUEST_HEADER
    if not adv.is_on_adventure(userid):
        try:
            name = get_attr(questid)
        except KeyError:
            return f"Error: 1uest number {questid} does not refer to any quest."
        if has_quest_reqs(userid, questid):
            if int(questid) not in set(users.get_completed_quests(userid)):
                if has_item_reqs(userid, questid):
                    required_items = get_attr(questid, key=ITEM_REQ_KEY)
                    loot = []
                    for item in required_items:
                        loot.extend(required_items[item] * [item])
                    users.update_inventory(userid, loot, remove=True)
                    chance = calc_chance(userid, questid)
                    quest_length = calc_length(userid, questid)
                    quest = adv.format_line(2, userid, adv.get_finish_time(quest_length), questid, chance)
                    adv.write(quest)
                    out += print_quest(questid, quest_length, chance)
                else:
                    return "Error: you do not have all the required items to start this quest."
            else:
                return "Error: you have already done this quest."
        else:
            return "Error: you have not completed the required quests to do this quest."
    else:
        out = adv.print_adventure(userid)
        out += adv.print_on_adventure_error('quest')
    return out
