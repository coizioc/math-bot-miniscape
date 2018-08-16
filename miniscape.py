"""Implements commands related to running a freemium-style text-based RPG."""
import asyncio
import random
import math
import itertools
import discord

from discord.ext import commands

import config
from subs.miniscape import adventures as adv
from subs.miniscape import deathmatch as dm
from subs.miniscape import craft
from subs.miniscape import items
from subs.miniscape import monsters as mon
from subs.miniscape import quests
from subs.miniscape import slayer
from subs.miniscape import users
from subs.miniscape import clues
from subs.miniscape import quiz

RESOURCES_DIRECTORY = f'./subs/miniscape/resources/'

PERMISSION_ERROR_STRING = f'Error: You do not have permission to use this command.'

ANNOUNCEMENTS_CHANNEL = 478965643862081546
NOTIFICATIONS_CHANNEL = 478967834198933524
ADVENTURES_CHANNEL = 478967314101043200
BANK_CHANNEL = 478967336653815835
SHOP_CHANNEL = 478967877517443073
DUEL_CHANNEL = 479056789330067457
JEOPARDY_CHANNEL = 479694071191961617
MINISCAPE_1_CHANNEL = 479668572344287238
MINISCAPE_2_CHANNEL = 479663988154695684
GENERAL_CHANNELS = [MINISCAPE_1_CHANNEL, MINISCAPE_2_CHANNEL]


class AmbiguousInputError(Exception):
    """Error raised for input that refers to multiple users"""
    def __init__(self, output):
        self.output = output


def get_member_from_guild(guild_members, username):
    """From a str username and a list of all guild members returns the member whose name contains username."""
    username = username.lower()
    if username == 'rand':
        return random.choice(guild_members)
    else:
        members = []
        for member in guild_members:
            if member.nick is not None:
                if username == member.nick.replace(' ', '').lower():
                    return member
                elif username in member.nick.replace(' ', '').lower():
                    members.append(member)
            elif username == member.name.replace(' ', '').lower():
                return member
            elif username in member.name.replace(' ', '').lower():
                members.append(member)

        members_len = len(members)
        if members_len == 0:
            raise NameError(username)
        elif members_len == 1:
            return members[0]
        else:
            raise AmbiguousInputError([member.name for member in members])


def get_display_name(member):
    """Gets the displayed name of a user."""
    if member.nick is None:
        name = member.name
    else:
        name = member.nick
    if users.read_user(member.id, key=users.IRONMAN_KEY):
        name += ' (IM)'
    return name


def parse_name(guild, username):
    """Gets the username of a user from a string and guild."""
    if '@' in username:
        try:
            return guild.get_member(int(username[3:-1]))
        except:
            raise NameError(username)
    else:
        return get_member_from_guild(guild.members, username)


class Miniscape():
    """Defines Miniscape commands."""

    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.check_adventures())
        self.bot.loop.create_task(self.backup_users())

    @commands.command()
    async def snap(self, ctx, *args):
        """Determines whether you have been snapped by Thanos or not."""
        if len(args) > 0:
            name = ' '.join(args)
        else:
            name = get_display_name(ctx.author)
        total = 0
        for c in name:
            total += ord(c)
        if total % 2 == 0:
            await ctx.send(f"{name.title()}, you were spared by Thanos.")
        else:
            await ctx.send(f'{name.title()}, you were slain by Thanos, for the good of the Universe.')

    @commands.group(invoke_without_command=True)
    async def me(self, ctx):
        """Shows information related to the user."""
        if ctx.channel.id == BANK_CHANNEL or ctx.channel.id in GENERAL_CHANNELS:
            name = get_display_name(ctx.author)
            await ctx.send(users.print_account(ctx.author.id, name))

    @me.group(name='stats', aliases=['levels'])
    async def _stats(self, ctx):
        """Shows the levels and stats of a user."""
        if ctx.channel.id == BANK_CHANNEL or ctx.channel.id in GENERAL_CHANNELS:
            name = get_display_name(ctx.author)
            await ctx.send(users.print_account(ctx.author.id, name, printequipment=False))

    @me.group(name='equipment', aliases=['armour', 'armor'])
    async def _equipment(self, ctx):
        if ctx.channel.id == BANK_CHANNEL or ctx.channel.id in GENERAL_CHANNELS:
            name = get_display_name(ctx.author)
            await ctx.send(users.print_equipment(ctx.author.id, name=name, with_header=True))

    @me.group(name='monsters')
    async def _monsters(self, ctx):
        """Shows how many monsters a user has killed."""
        if ctx.channel.id == BANK_CHANNEL or ctx.channel.id in GENERAL_CHANNELS:
            name = get_display_name(ctx.author)
            out = mon.print_monster_kills(ctx.author.id, name)
            await ctx.send(out)

    @me.command(name='clues')
    async def _clues(self, ctx):
        """Shows how many clue scrolls a user has completed."""
        if ctx.channel.id == BANK_CHANNEL or ctx.channel.id in GENERAL_CHANNELS:
            out = clues.print_clue_scrolls(ctx.author.id)
            await ctx.send(out)

    @commands.command(aliases=['lookup', 'finger', 'find'])
    async def examine(self, ctx, *args):
        """Examines a given user."""
        if ctx.channel.id == BANK_CHANNEL or ctx.channel.id in GENERAL_CHANNELS:
            search_string = ' '.join(args).lower()
            for member in ctx.guild.members:
                if member.nick is not None:
                    if search_string in member.nick.lower():
                        name = member.nick
                        break
                if search_string in member.name.lower():
                    name = member.name
                    break
            else:
                await ctx.send(f'Could not find {search_string} in server.')
                return

            await ctx.send(users.print_account(member.id, name))

    @commands.command()
    async def equip(self, ctx, *args):
        """Equips an item from a user's inventory."""
        if ctx.channel.id == BANK_CHANNEL or ctx.channel.id in GENERAL_CHANNELS:
            item = ' '.join(args)
            out = users.equip_item(ctx.author.id, item.lower())
            await ctx.send(out)

    @commands.command()
    async def unequip(self, ctx, *args):
        """Unequips an item from a user's equipment."""
        if ctx.channel.id == BANK_CHANNEL or ctx.channel.id in GENERAL_CHANNELS:
            item = ' '.join(args)
            out = users.unequip_item(ctx.author.id, item.lower())
            await ctx.send(out)

    @commands.group(aliases=['invent', 'inventory', 'item'], invoke_without_command=True)
    async def items(self, ctx, search=''):
        """Show's the player's inventory."""
        if ctx.channel.id in [BANK_CHANNEL, SHOP_CHANNEL] or ctx.channel.id in GENERAL_CHANNELS:
            inventory = users.print_inventory(ctx.author, search.lower())
            count = 1
            for message in inventory:
                message += f' *{count}/{len(inventory)}*'
                await ctx.send(message)
                count += 1

    @items.command(name='info')
    async def _item_info(self, ctx, *args):
        item = ' '.join(args)
        if ctx.channel.id == BANK_CHANNEL or ctx.channel.id in GENERAL_CHANNELS:
            out = items.print_stats(item)
            await ctx.send(out)

    @commands.command()
    async def slayer(self, ctx):
        """Gives the user a slayer task."""
        if ctx.channel.id == ADVENTURES_CHANNEL or ctx.channel.id in GENERAL_CHANNELS:
            out = slayer.get_task(ctx.author.id)
            await ctx.send(out)

    @commands.command()
    async def reaper(self, ctx):
        """Gives the user a reaper task."""
        if ctx.channel.id == ADVENTURES_CHANNEL or ctx.channel.id in GENERAL_CHANNELS:
            out = slayer.get_reaper_task(ctx.author.id)
            await ctx.send(out)

    @commands.group(invoke_without_command=True, aliases=['grind', 'fring'])
    async def kill(self, ctx, *args):
        """Lets the user kill monsters for a certain number or a certain amount of time."""
        if ctx.channel.id == ADVENTURES_CHANNEL or ctx.channel.id in GENERAL_CHANNELS:
            if len(args) > 0:
                monster = ''
                if args[0].isdigit():
                    number = args[0]
                    monster = ' '.join(args[1:])
                    out = slayer.get_kill(ctx.author.id, monster, number=number)
                elif args[-1].isdigit():
                    length = args[-1]
                    monster = ' '.join(args[:-1])
                    out = slayer.get_kill(ctx.author.id, monster, length=length)
                else:
                    monster = ' '.join(args)
                    if monster == 'myself':
                        with open('./subs/miniscape/resources/hotlines.txt', 'r') as f:
                            lines = f.read().splitlines()
                        out = '**If you need help, please call one of the following numbers**:\n'
                        for line in lines:
                            out += f'{line}\n'
                    else:
                        out = 'Error: there must be a number or length of kill in args.'
            else:
                if adv.is_on_adventure(ctx.author.id):
                    out = slayer.get_kill(ctx.author.id, 'GET_UPDATE')
                else:
                    out = 'args not valid. Please put in the form `[number] [monster name] [length]`'
            await ctx.send(out)

    @commands.command(aliases=['starter'])
    async def starter_gear(self, ctx):
        """Gives the user a set of bronze armour."""
        if ctx.channel.id == SHOP_CHANNEL or ctx.channel.id == ADVENTURES_CHANNEL or ctx.channel.id in GENERAL_CHANNELS:
            name = get_display_name(ctx.author)
            if users.read_user(ctx.author.id, key=users.COMBAT_XP_KEY) == 0:
                users.update_inventory(ctx.author.id, [63, 66, 69, 70, 64, 72])

                await ctx.send(f'Bronze set given to {name}! You can see your items by typing `~inventory` in #bank '
                               f'and equip them by typing `~equip [item]`. You can see your current stats by typing '
                               f'`~me`. If you need help with commands, feel free to look at #welcome or ask around!')
            else:
                await ctx.send(f'You are too experienced to get the starter gear, {name}.')

    @commands.command(aliases=['bes', 'monsters'])
    async def bestiary(self, ctx, *args):
        """Shows a list of monsters and information related to those monsters."""
        if ctx.channel.id == BANK_CHANNEL or ctx.channel.id in GENERAL_CHANNELS:
            monster = ' '.join(args)
            if monster == '':
                messages = mon.print_list()
            else:
                messages = mon.print_monster(monster)
            for message in messages:
                await ctx.send(message)

    @commands.command()
    async def chance(self, ctx, monsterid, dam=-1, acc=-1, arm=-1, cb=-1, xp=-1, num=100, dfire=False):
        # if len(args) == 1:
        #     monsterid = int(args[0])
        # elif len(args == 4):

        out = slayer.print_chance(ctx.author.id, monsterid, monster_dam=int(dam), monster_acc=int(acc),
                                  monster_arm=int(arm), monster_combat=int(cb), xp=int(xp), number=int(num),
                                  dragonfire=bool(dfire))
        await ctx.send(out)

    @commands.command()
    async def claim(self, ctx, *args):
        if ctx.channel.id == BANK_CHANNEL or ctx.channel.id in GENERAL_CHANNELS:
            if args[0].isdigit():
                number = int(args[0])
                item = ' '.join(args[1:])
            else:
                number = 1
                item = ' '.join(args)
            out = items.claim(ctx.author.id, item, number)
            await ctx.send(out)

    @commands.command()
    async def cancel(self, ctx):
        """Cancels your current action."""
        try:
            task = adv.get_adventure(ctx.author.id)

            adventureid = task[0]
            if adventureid == '0':
                if users.item_in_inventory(ctx.author.id, '291'):
                    users.update_inventory(ctx.author.id, ['291'], remove=True)
                    adv.remove(ctx.author.id)
                    out = 'Slayer task cancelled!'
                else:
                    out = 'Error: You do not have a reaper token.'
            elif adventureid == '1':
                adv.remove(ctx.author.id)
                out = 'Killing session cancelled!'
            elif adventureid == '2':
                adv.remove(ctx.author.id)
                out = 'Quest cancelled!'
            elif adventureid == '3':
                adv.remove(ctx.author.id)
                out = 'Gather cancelled!'
            elif adventureid == '4':
                adv.remove(ctx.author.id)
                out = 'Clue scroll cancelled!'
            elif adventureid == '5':
                adv.remove(ctx.author.id)
                out = 'Reaper task cancelled!'
            else:
                out = f'Error: Invalid Adventure ID {adventureid}'

        except NameError:
            out = 'You are not currently doing anything.'
        await ctx.send(out)

    @commands.command()
    async def compare(self, ctx, item1, item2):
        """Compares the stats of two items."""
        if ctx.channel.id == BANK_CHANNEL or ctx.channel.id in GENERAL_CHANNELS:
            out = items.compare(item1.lower(), item2.lower())
            await ctx.send(out)

    @commands.command()
    async def status(self, ctx):
        """Says what you are currently doing."""
        if ctx.channel.id == ADVENTURES_CHANNEL or ctx.channel.id in GENERAL_CHANNELS:
            if adv.is_on_adventure(ctx.author.id):
                out = adv.print_adventure(ctx.author.id)
            else:
                out = 'You are not doing anything at the moment.'
            await ctx.send(out)

    @commands.group(aliases=['clues'], invoke_without_command=True)
    async def clue(self, ctx, difficulty):
        """Starts a clue scroll."""
        if ctx.channel.id == ADVENTURES_CHANNEL or ctx.channel.id in GENERAL_CHANNELS:
            if not difficulty.isdigit():
                difficulty_names = {
                    'easy': 1,
                    'medium': 2,
                    'hard': 3,
                    'elite': 4,
                    'master': 5
                }
                if difficulty not in set(difficulty_names.keys()):
                    await ctx.send(f'Error: {difficulty} not valid clue scroll difficulty.')
                    return
                else:
                    parsed_difficulty = difficulty_names[difficulty]
            else:
                if not (0 < int(difficulty) < 6):
                    await ctx.send(f'Error: {difficulty} not valid clue scroll difficulty.')
                    return
                else:
                    parsed_difficulty = int(difficulty)
            out = clues.start_clue(ctx.author.id, parsed_difficulty)
            await ctx.send(out)

    @commands.command(aliases=['drank', 'chug', 'suckle'])
    async def drink(self, ctx, *args):
        """Drinks a potion."""
        if ctx.channel.id in {BANK_CHANNEL, ADVENTURES_CHANNEL} or ctx.channel.id in GENERAL_CHANNELS:
            name = ' '.join(args)
            out = items.drink(ctx.author.id, name)
            await ctx.send(out)

    @commands.group(invoke_without_command=True)
    async def shop(self, ctx):
        """Shows the items available at the shop."""
        if ctx.channel.id == SHOP_CHANNEL or ctx.channel.id in GENERAL_CHANNELS:
            messages = items.print_shop(ctx.author.id)
            for message in messages:
                await ctx.send(message)

    @commands.command()
    async def buy(self, ctx, *args):
        """Buys something from the shop."""
        if ctx.channel.id == SHOP_CHANNEL or ctx.channel.id in GENERAL_CHANNELS:
            if len(args) > 0:
                if args[0].isdigit():
                    number = int(args[0])
                    item = ' '.join(args[1:])
                else:
                    number = 1
                    item = ' '.join(args)
                out = items.buy(ctx.author.id, item, number=number)
                await ctx.send(out)

    @commands.command()
    async def sell(self, ctx, *args):
        """Sells the player's inventory for GasterCoin."""
        if ctx.channel.id == SHOP_CHANNEL or ctx.channel.id in GENERAL_CHANNELS:
            try:
                number = int(args[0])
                item = ' '.join(args[1:])
            except ValueError:
                number = 1
                item = ' '.join(args)
            out = items.sell(ctx.author.id, item, number=number)
            await ctx.send(out)

    @commands.command()
    async def sellall(self, ctx, maxvalue=None):
        """Sells all items in the player's inventory (below a certain value) for GasterCoin."""
        if ctx.channel.id == SHOP_CHANNEL or ctx.channel.id in GENERAL_CHANNELS:
            inventory = users.read_user(ctx.author.id, key=users.ITEMS_KEY)
            name = get_display_name(ctx.author)
            if maxvalue is None:
                value = users.get_value_of_inventory(inventory)
                users.update_inventory(ctx.author.id, value*["0"])
                users.clear_inventory(ctx.author.id)
                value_formatted = '{:,}'.format(value)
                maxvalue_formatted = '{:,}'.format(int(maxvalue))
                name = get_display_name(ctx.author)
                out = f"All items in {name}'s inventory worth under {maxvalue_formatted} coins "\
                      f"sold for {value_formatted} coins!"
            else:
                value = users.get_value_of_inventory(inventory, under=maxvalue)
                users.update_inventory(ctx.author.id, value * ["0"])
                users.clear_inventory(ctx.author.id, under=maxvalue)
                value_formatted = '{:,}'.format(value)
                out = f"All items in {name}'s inventory "\
                      f"sold for {value_formatted} coins!"
            await ctx.send(out)

    @commands.command()
    async def trade(self, ctx, *args):
        """Trades to a person a number of a given object for a given price."""
        if ctx.channel.id == SHOP_CHANNEL or ctx.channel.id in GENERAL_CHANNELS:
            if users.read_user(ctx.author.id, key=users.IRONMAN_KEY):
                await ctx.send('Ironmen cannot trade.')
                return

            if len(args) < 4:
                await ctx.send('Arguments missing. Syntax is `~trade [name] [number] [item] [offer]`.')
                return

            name = args[0]
            for member in ctx.guild.members:
                if name.lower() in member.name.lower():
                    name_member = member
                    break
            else:
                await ctx.send(f'{name} not found in server.')
                return
            if users.read_user(name_member.id, key=users.IRONMAN_KEY):
                await ctx.send('You cannot trade with an ironman.')
                return

            try:
                number = int(args[1])
            except ValueError:
                await ctx.send(f'{args[1]} is not a valid number.')
                return

            try:
                offer = users.parse_int(args[-1])
                itemid = items.find_by_name(' '.join(args[2:-1]))
            except ValueError:
                await ctx.send(f'{args[-1]} is not a valid offer.')
                return
            except KeyError:
                await ctx.send(f"{' '.join(args[2:-1])} is not a valid item.")
                return

            if not users.item_in_inventory(ctx.author.id, itemid, number):
                await ctx.send(f'You do not have {items.add_plural(number, itemid)} in your inventory.')
                return

            if not items.is_tradable(itemid):
                await ctx.send(f'You can not trade this item. ({items.get_attr(itemid)})')
                return

            if not users.item_in_inventory(name_member.id, "0", offer):
                await ctx.send(f'{get_display_name(name_member)} does not have enough gold to buy this many items.')
                return

            name = get_display_name(ctx.author)
            offer_formatted = '{:,}'.format(offer)
            out = f'{items.SHOP_HEADER}{name.title()} wants to sell {name_member.mention} ' \
                  f'{items.add_plural(number, itemid)} for {offer_formatted} coins. To accept this offer, reply ' \
                  f'to this post with a :thumbsup:. Otherwise, this offer will expire in one minute.'
            msg = await ctx.send(out)
            await msg.add_reaction('\N{THUMBS UP SIGN}')

            while True:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=60)
                    if str(reaction.emoji) == '👍' and user == name_member and reaction.message.id == msg.id:
                        price = offer*["0"]
                        users.update_inventory(name_member.id, price, remove=True)
                        users.update_inventory(ctx.author.id, price)
                        loot = number * [itemid]
                        users.update_inventory(ctx.author.id, loot, remove=True)
                        users.update_inventory(name_member.id, loot)

                        buyer_name = get_display_name(name_member)
                        await ctx.send(f'{items.SHOP_HEADER}{name.title()} successfully sold '
                                       f'{items.add_plural(number, itemid)} to {buyer_name} for '
                                       f'{offer_formatted} coins!')
                        return
                except asyncio.TimeoutError:
                    await msg.edit(content=f'One minute has passed and your offer has been cancelled.')
                    return

    @commands.command()
    async def ironman(self, ctx):
        """Lets a user become an ironman, by the way."""
        out = ':tools: __**IRONMAN**__ :tools:\n' \
              'If you want to become an ironman, please react to this post with a :thumbsup:. ' \
              'This will **RESET** your account and give you the ironman role. ' \
              'You will be unable to trade with other players or gamble. ' \
              'In return, you will be able to proudly display your status as an ironman, by the way.'
        msg = await ctx.send(out)
        await msg.add_reaction('\N{THUMBS UP SIGN}')

        while True:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60)
                if str(reaction.emoji) == '👍' and user == ctx.author and reaction.message.id == msg.id:
                    users.reset_account(ctx.author.id)
                    users.update_user(ctx.author.id, True, key=users.IRONMAN_KEY)
                    ironman_role = discord.utils.get(ctx.guild.roles, name="Ironman")
                    await ctx.author.add_roles(ironman_role, reason='Wanted to become an ironmeme.')
                    name = get_display_name(ctx.author)
                    await msg.edit(content=f':tools: __**IRONMAN**__ :tools:\nCongratulations, {name}, you are now '
                                   'an ironman!')
                    return
            except asyncio.TimeoutError:
                await msg.edit(content=f'Your request has timed out. Please retype the command to try again.')
                return

    @commands.group(invoke_without_command=True, aliases=['quest'])
    async def quests(self, ctx, questid=None):
        if ctx.channel.id == ADVENTURES_CHANNEL or ctx.channel.id in GENERAL_CHANNELS:
            if questid is not None:
                out = quests.print_details(ctx.author.id, questid)
            else:
                out = quests.print_list(ctx.author.id)
            await ctx.send(out)

    @quests.command(name='start')
    async def _start(self, ctx, questid):
        """lets a user start a quest."""
        if ctx.channel.id == ADVENTURES_CHANNEL or ctx.channel.id in GENERAL_CHANNELS:
            out = quests.start_quest(ctx.author.id, questid)
            await ctx.send(out)

    @commands.command()
    async def gather(self, ctx, *args):
        """Gathers items."""
        if ctx.channel.id == ADVENTURES_CHANNEL or ctx.channel.id in GENERAL_CHANNELS:
            if len(args) > 0:
                if args[0].isdigit():
                    number = args[0]
                    item = ' '.join(args[1:])
                    out = craft.start_gather(ctx.author.id, item, number=number)
                elif args[-1].isdigit():
                    length = args[-1]
                    item = ' '.join(args[:-1])
                    out = craft.start_gather(ctx.author.id, item, length=length)
                else:
                    out = 'Error: there must be a number or length of gathering in args.'

            else:
                if adv.is_on_adventure(ctx.author.id):
                    out = slayer.get_kill(ctx.author.id, 'GET_UPDATE')
                else:
                    out = 'args not valid. Please put in the form `[number] [item name] [length]`'
            await ctx.send(out)

    @commands.group(invoke_without_command=True, aliases=['recipe'])
    async def recipes(self, ctx):
        """Prints a list of recipes a user can create."""
        if ctx.channel.id == BANK_CHANNEL or ctx.channel.id in GENERAL_CHANNELS:
            messages = craft.print_list(ctx.author.id)
            for message in messages:
                await ctx.send(message)

    @recipes.command(name='info')
    async def _recipe_info(self, ctx, *args):
        """Lists the details of a particular recipe."""
        if ctx.channel.id == BANK_CHANNEL or ctx.channel.id in GENERAL_CHANNELS:
            recipe = ' '.join(args)
            out = craft.print_recipe(ctx.author.id, recipe)
            await ctx.send(out)

    @commands.command()
    async def craft(self, ctx, *args):
        if ctx.channel.id == BANK_CHANNEL or ctx.channel.id in GENERAL_CHANNELS:
            try:
                number = int(args[0])
                recipe = ' '.join(args[1:])
            except ValueError:
                number = 1
                recipe = ' '.join(args)
            out = craft.craft(ctx.author.id, recipe, n=number)
            await ctx.send(out)

    @commands.command(aliases=['cock', 'fry', 'grill', 'saute', 'boil'])
    async def cook(self, ctx, *args):
        if ctx.channel.id == BANK_CHANNEL or ctx.channel.id in GENERAL_CHANNELS:
            try:
                number = int(args[0])
                food = ' '.join(args[1:])
            except ValueError:
                number = 1
                food = ' '.join(args)
            out = craft.cook(ctx.author.id, food, n=number)
            await ctx.send(out)

    @commands.group(aliases=['nq', 'jeo'], invoke_without_command=True)
    async def jeopardy(self, ctx, textonly='f'):
        """Gives users GasterCash in exchange for correct answers."""
        if ctx.channel.id == JEOPARDY_CHANNEL:
            question_args = quiz.get_new_question()
            category = question_args[0]
            value = question_args[1]
            question = question_args[2]
            answer = question_args[3]

            if textonly != 't':
                quiz.draw_jeopardy(question)
                await ctx.send(f"*{ctx.author.name}: I'll take {category} for {value} coins, Alex.*",
                               file=discord.File(quiz.OUT_FILE))
            else:
                await ctx.send(f"*{ctx.author.name}: I'll take {category} for {value} coins, Alex.*\n{question}")

            while True:
                message = await self.bot.wait_for('message')
                if message.author == ctx.author:
                    if message.content.lower() in answer.lower() and len(message.content) > 1:
                        amount_formatted = '{:,}'.format(value)

                        out = f"Answer {answer} is correct! "
                        if not users.read_user(ctx.author.id, key=users.IRONMAN_KEY):
                            users.update_inventory(ctx.author.id, value * ['0'])
                            out += f"{ctx.author.name}'s balance has increased by {amount_formatted} coins!"
                        await ctx.send(out)
                        break
                    else:
                        await ctx.send(f"Answer {message.content} is incorrect. Correct answer was {answer}.")
                        break

    @commands.group(aliases=['dm'], invoke_without_command=True)
    async def deathmatch(self, ctx, opponent='rand', bet=None):
        """Allows users to duke it out in a 1v1 match."""
        if ctx.channel.id == DUEL_CHANNEL or ctx.channel.id in GENERAL_CHANNELS:
            author_name = get_display_name(ctx.author)
            if bet is not None:
                if users.read_user(ctx.author.id, key=users.IRONMAN_KEY):
                    await ctx.send('Ironmen cannot start staked deathmatches.')
                    return
                try:
                    bet = users.parse_int(bet)
                except ValueError:
                    await ctx.send(f'{bet} does not represent a valid number.')
                bet_formatted = '{:,}'.format(bet)
                if not users.item_in_inventory(ctx.author.id, '0', bet):
                    await ctx.send(f'You do not have {bet_formatted} coins.')
                    return
                try:
                    opponent_member = parse_name(ctx.message.guild, opponent)
                except NameError:
                    await ctx.send(f'{opponent} not found in server.')
                    return
                except AmbiguousInputError as members:
                    await ctx.send(f'Input {opponent} can refer to multiple people ({members})')
                    return
                if users.read_user(opponent_member.id, key=users.IRONMAN_KEY):
                    await ctx.send('You cannot start a staked deathmatch with an ironman.')
                    return
                bet_formatted = '{:,}'.format(bet)
                opponent_name = get_display_name(opponent_member)
                if not users.item_in_inventory(opponent_member.id, '0', bet):
                    await ctx.send(f'{opponent_name} does not have {bet_formatted} coins.')
                    return
                users.update_inventory(ctx.author.id, bet*['0'], remove=True)
                out = f'Deathmatch set up between {author_name} and {opponent_member.mention} with bet ' \
                      f'{bet_formatted} coins! To confirm this match, {opponent_name} must react to ' \
                      f'this message with a :thumbsup: in the next minute. If a minute passes or if the ' \
                      f'challenger reacts to this message, the deathmatch will be cancelled and the deposit ' \
                      f'refunded.'
                msg = await ctx.send(out)
                await msg.add_reaction('\N{THUMBS UP SIGN}')

                while True:
                    try:
                        reaction, user = await self.bot.wait_for('reaction_add', timeout=60)
                        if str(reaction.emoji) == '👍' and user == opponent_member:
                            users.update_inventory(opponent_member.id, bet*['0'], remove=True)
                            deathmatch_messages = dm.do_deathmatch(ctx.author, opponent_member,
                                                                   bet=bet_formatted)
                            for message in deathmatch_messages[:-1]:
                                await msg.edit(content=message)
                                await asyncio.sleep(1)
                            users.update_inventory(deathmatch_messages[-1], 2 * bet * ['0'])
                            return
                        elif user == ctx.author:
                            users.update_inventory(ctx.author.id, bet * ['0'])
                            await msg.edit(content=f'{author_name} has declined their challenge and '
                                                   f'the deposit of {bet_formatted} coins has been returned.')
                            return
                    except asyncio.TimeoutError:
                        users.update_inventory(ctx.author.id, bet * ['0'])
                        await msg.edit(content=f'One minute has passed and the deathmatch has been cancelled. '
                                               f'The deposit of {bet_formatted} coins has been returned.')
                        return
            else:
                try:
                    opponent_member = parse_name(ctx.message.guild, opponent)
                except NameError:
                    await ctx.send(f'{opponent} not found in server.')
                    return
                except AmbiguousInputError as members:
                    await ctx.send(f'Input {opponent} can refer to multiple people ({members})')
                    return
                msg = await ctx.send(dm.DEATHMATCH_HEADER)
                deathmatch_messages = dm.do_deathmatch(ctx.author, opponent_member)
                for message in deathmatch_messages[:-1]:
                    await msg.edit(content=message)
                    await asyncio.sleep(1)

    @commands.command()
    async def balance(self, ctx, name=None):
        """Checks the user's balance."""
        if name is None:
            amount = '{:,}'.format(users.get_coins_in_inventory(ctx.author.id))
            name = get_display_name(ctx.author)
            await ctx.send(f'{name} has {amount} coins')
        elif name == 'universe':
            await ctx.send('As all things should be.')
        else:
            try:
                person_member = parse_name(ctx.message.guild, name)
                name = get_display_name(person_member)
                amount = '{:,}'.format(users.get_coins_in_inventory(ctx.author.id))
                await ctx.send(f'{name} has {amount} coins')
            except NameError:
                await ctx.send(f'Name {name} not found in server.')
            except AmbiguousInputError as members:
                await ctx.send(f'Input {name} can refer to multiple people ({members})')

    @commands.command(aliases=['leaderboards'])
    async def leaderboard(self, ctx, *args):
        """Allows users to easily compare each others' stats."""
        if ctx.channel.id == BANK_CHANNEL or ctx.channel.id in GENERAL_CHANNELS:
            if len(args) == 0:
                name = None
                key = 'total'
            elif len(args) == 1:
                if 'key=' in args[0]:
                    name = None
                    for userkey in users.DEFAULT_ACCOUNT.keys():
                        if args[0][4:] in userkey:
                            key = userkey
                            break
                    else:
                        if args[0][4:] == 'total':
                            key = 'total'
                        else:
                            await ctx.send(f'Key {args[0]} not found.')
                            return

                else:
                    name = args[0]
                    key = 'total'
            else:
                key = args[0]
                if key not in users.DEFAULT_ACCOUNT.keys():
                    if key != 'total':
                        await ctx.send(f'Key {key} not found.')
                        return
                name = ' '.join(args[1:])

            key_name = {
                users.ITEMS_KEY: 'gold',
                users.SLAYER_XP_KEY: 'slayer',
                users.COMBAT_XP_KEY: 'combat',
                users.GATHER_XP_KEY: 'gather',
                users.ARTISAN_XP_KEY: 'artisan',
                users.COOK_XP_KEY: 'cooking',
                users.QUESTS_KEY: 'quest points',
                'total': 'total level'
            }
            if key not in key_name.keys():
                await ctx.send(f"Can't make leaderboard with key {key}.")
                return

            leaderboard = users.get_values_by_account(key=key)

            out = f':hammer_pick: __**{key.upper()} LEADERBOARD**__ :crossed_swords:\n'
            if name is None:
                try:
                    for i in range(10):
                        user_id, amount = leaderboard[i]
                        amount_formatted = '{:,}'.format(amount)
                        member = ctx.message.guild.get_member(user_id)
                        if member is not None:
                            name = get_display_name(member)
                        else:
                            name = f'User {user_id}'
                        out += f'**({1 + i}) {name}**: '
                        if key == users.ITEMS_KEY:
                            out += f'{amount_formatted}  coins\n'
                        elif key == users.QUESTS_KEY:
                            out += f'{amount_formatted} quests\n'
                        elif key == 'total':
                            out += f'{amount_formatted} levels\n'
                        else:
                            out += f'{users.xp_to_level(amount)} *({amount_formatted}xp)*\n'
                except IndexError:
                    pass
                await ctx.send(out)
            else:
                if name == 'bottom':
                    try:
                        for i in range(len(leaderboard) - 10, len(leaderboard)):
                            user_id, amount = leaderboard[i]
                            amount_formatted = '{:,}'.format(amount)
                            member = ctx.message.guild.get_member(user_id)
                            if member is not None:
                                name = get_display_name(member)
                            else:
                                name = f'User {user_id}'
                            out += f'**({1 + i}) {name}**: '
                            if key == users.ITEMS_KEY:
                                out += f'{amount_formatted}  coins\n'
                            elif key == users.QUESTS_KEY:
                                out += f'{amount_formatted} quests\n'
                            elif key == 'total':
                                out += f'{amount_formatted} levels\n'
                            else:
                                out += f'{users.xp_to_level(amount)} *({amount_formatted}xp)*\n'
                    except IndexError:
                        pass
                    await ctx.send(out)
                else:
                    try:
                        name_list = [x[0] for x in leaderboard]
                        name_member = parse_name(ctx.message.guild, name)
                        name_index = name_list.index(name_member.id)
                        if name_index < 5:
                            lower = 0
                            upper = 10
                        else:
                            lower = name_index - 5
                            upper = name_index + 5
                        if name_index + 5 > len(leaderboard):
                            upper = len(leaderboard)
                            lower = len(leaderboard) - 10
                        for i in range(lower, upper):
                            user_id, amount = leaderboard[i]
                            amount_formatted = '{:,}'.format(amount)
                            member = ctx.message.guild.get_member(user_id)
                            if member is not None:
                                name = get_display_name(member)
                            else:
                                name = f'User {user_id}'
                            out += f'**({1 + i}) {name}**: '
                            if key == users.ITEMS_KEY:
                                out += f'{amount_formatted}  coins\n'
                            elif key == users.QUESTS_KEY:
                                out += f'{amount_formatted} quests\n'
                            elif key == 'total':
                                out += f'{amount_formatted} levels\n'
                            else:
                                out += f'{users.xp_to_level(amount)} *({amount_formatted}xp)*\n'
                    except IndexError:
                        pass
                    except ValueError:
                        await ctx.send(f'Name {name} not found in leaderboard.')
                    await ctx.send(out)

    async def backup_users(self):
        """Backs up the userjson files into another directory."""
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            users.backup()
            await asyncio.sleep(3600)

    async def check_adventures(self):
        """Check if any actions are complete and notifies the user if they are done."""
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            finished_tasks = adv.get_finished()
            for task in finished_tasks:
                with open('./subs/miniscape/resources/finished_tasks.txt', 'a+') as f:
                    f.write(';'.join(task) + '\n')
                adventureid, userid = int(task[0]), int(task[1])
                bot_self = self.bot.get_guild(config.guild_id).get_channel(NOTIFICATIONS_CHANNEL)
                person = self.bot.get_guild(config.guild_id).get_member(int(userid))

                adventures = {
                    0: slayer.get_result,
                    1: slayer.get_kill_result,
                    2: quests.get_result,
                    3: craft.get_gather,
                    4: clues.get_clue_scroll,
                    5: slayer.get_reaper_result
                }
                out = adventures[adventureid](person, task[3:])
                await bot_self.send(out)
            await asyncio.sleep(60)


def setup(bot):
    """Adds the cog to the bot."""
    bot.add_cog(Miniscape(bot))
