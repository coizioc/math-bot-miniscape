"""Implements commands related to running a freemium-style text-based RPG."""
import asyncio
import random
import math
import itertools

from discord.ext import commands

import config
from subs.gastercoin import account as ac
from subs.miniscape import adventures as adv
from subs.miniscape import craft
from subs.miniscape import items
from subs.miniscape import monsters as mon
from subs.miniscape import quests
from subs.miniscape import slayer
from subs.miniscape import users
from subs.miniscape import clues

RESOURCES_DIRECTORY = f'./subs/miniscape/resources/'

PERMISSION_ERROR_STRING = f'Error: You do not have permission to use this command.'

COMBAT_CHANNEL = 471440571207254017
BANK_CHANNEL = 471440651620319233
SHOP_CHANNEL = 471445748995850240
ANNOUNCEMENTS_CHANNEL = 471814213300518933


class Miniscape():
    """Defines Miniscape commands."""

    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.check_adventures())

    @commands.command()
    async def ship(self, ctx, *args):
        if len(args) == 1:
            person1 = ctx.author.name.lower().replace(' ', '')
            person2 = args[0].lower().replace(' ', '')
        elif len(args) == 2:
            person1 = args[0].lower().replace(' ', '')
            person2 = args[1].lower().replace(' ', '')
        else:
            return
        total = 0

        for name in [person1, person2]:
            for c in name:
                total += ord(c)
        percent = (total + 32) % 101
        out = f':heartpulse: __**MATCHMAKING**__ :heartpulse:\n'\
              f':small_red_triangle_down: *`{person1}`*\n'\
              f':small_red_triangle: *`{person2}`*\n\n'\
              f'**{percent}%** ​`'

        percent_bars = int(math.floor(percent / 10))
        for _ in range(percent_bars):
            out += '█'
        for _ in range(10 - percent_bars):
            out += ' ​'
        out += '`\n\n'

        descriptions = {
            9: 'Awful :sob:',
            19: 'Bad :cry:',
            29: 'Pretty low :frowning:',
            39: 'Not Too Great :confused:',
            49: 'Worse Than Average :neutral_face:',
            59: 'Barely :no_mouth:',
            68: 'Not Bad :slight_smile:',
            69: '( ͡° ͜ʖ ͡°)',
            79: 'Pretty Good :smiley:',
            89: 'Great :smile:',
            99: 'Amazing :heart_eyes:',
            100: 'PERFECT! :heart_exclamation:'
        }

        for max_value in descriptions.keys():
            if percent <= max_value:
                description_text = descriptions[max_value]
                break
        else:
            description_text = descriptions[100]
        out += description_text
        await ctx.send(out)

    @commands.command()
    async def shipall(self, ctx, word, bottom=None):
        out = ':heartpulse: __**MATCHMAKING**__ :heartpulse:\n'
        word = word.lower().replace(' ', '')
        relationships = []
        guild_members = ctx.guild.members
        for member in guild_members:
            name = member.name.lower().replace(' ', '')
            total = 0

            for name in [word, name]:
                for c in name:
                    total += ord(c)
            percent = (total + 32) % 101
            relationships.append(tuple((percent, member)))
        if bottom is None:
            relationships = sorted(relationships, key=lambda x: x[0], reverse=True)
        else:
            relationships = sorted(relationships, key=lambda x: x[0])
        for i in range(10):
            out += f'**{i + 1}**: `{word}` :heart: `{relationships[i][1].name}`: {relationships[i][0]}%\n'
        await ctx.send(out)

    @commands.group(invoke_without_command=True)
    async def me(self, ctx):
        """Shows information related to the user."""
        if ctx.channel.id == BANK_CHANNEL:
            await ctx.send(users.print_account(ctx.author.id))

    @me.group(name='equip')
    async def _equip(self, ctx, *args):
        """Equips an item from a user's inventory."""
        if ctx.channel.id == BANK_CHANNEL:
            item = ' '.join(args)
            out = users.equip_item(ctx.author.id, item.lower())
            await ctx.send(out)

    @me.group(name='monsters')
    async def _monsters(self, ctx):
        """Shows how many monsters a user has killed."""
        if ctx.channel.id == BANK_CHANNEL:
            out = mon.print_monster_kills(ctx.author.id)
            await ctx.send(out)

    @me.command(name='clues')
    async def _clues(self, ctx):
        if ctx.channel.id == BANK_CHANNEL:
            out = clues.print_clue_scrolls(ctx.author.id)
            await ctx.send(out)

    @commands.group(aliases=['invent', 'inventory', 'item'], invoke_without_command=True)
    async def items(self, ctx, search=''):
        """Show's the player's inventory."""
        if ctx.channel.id == BANK_CHANNEL:
            inventory = users.print_inventory(ctx.author, search.lower())
            count = 1
            for message in inventory:
                message += f' *{count}/{len(inventory)}*'
                await ctx.send(message)
                count += 1

    @items.command(name='stats', aliases=['stat', 'info'])
    async def _stats(self, ctx, *args):
        item = ' '.join(args)
        if ctx.channel.id == BANK_CHANNEL:
            out = items.print_stats(item)
            await ctx.send(out)

    @commands.group(invoke_without_command=True)
    async def slayer(self, ctx):
        """Gives the user a slayer task."""
        if ctx.channel.id == COMBAT_CHANNEL:
            out = slayer.get_task(ctx.author.id)
            await ctx.send(out)

    @commands.group(invoke_without_command=True, aliases=['grind', 'fring'])
    async def kill(self, ctx, *args):
        """Lets the user kill monsters for a certain number or a certain amount of time."""
        if ctx.channel.id == COMBAT_CHANNEL:
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
        if ctx.channel.id == SHOP_CHANNEL or ctx.channel.id == COMBAT_CHANNEL:
            if users.read_user(ctx.author.id, key=users.COMBAT_XP_KEY) == 0:
                users.update_inventory(ctx.author.id, [63, 66, 69, 70])
                await ctx.send(f'Bronze set given to {ctx.author.name}! You can see your items by typing `~inventory` '
                               f'and equip them by typing `~me equip [item]`. You can see your current stats by typing '
                               f'`~me`.')
            else:
                await ctx.send(f'You are too experienced to get the starter gear, {ctx.author.name}.')

    @commands.command(aliases=['bes', 'monsters'])
    async def bestiary(self, ctx, *args):
        """Shows a list of monsters and information related to those monsters."""
        if ctx.channel.id == BANK_CHANNEL:
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
    async def claim(self, ctx, item):
        out = items.claim(item)
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
            else:
                out = f'Error: Invalid Adventure ID {adventureid}'

        except NameError:
            out = 'You are not currently doing anything.'
        await ctx.send(out)

    @commands.command()
    async def compare(self, ctx, item1, item2):
        """Compares the stats of two items."""
        if ctx.channel.id == BANK_CHANNEL:
            out = items.compare(item1.lower(), item2.lower())
            await ctx.send(out)

    @commands.command()
    async def status(self, ctx):
        """Tells what you are currently doing."""
        if ctx.channel.id == COMBAT_CHANNEL:
            if adv.is_on_adventure(ctx.author.id):
                out = adv.print_adventure(ctx.author.id)
            else:
                out = 'Cheq is a dumb bitch.'
            await ctx.send(out)

    @commands.group(aliases=['clues'], invoke_without_command=True)
    async def clue(self, ctx, difficulty):
        """Starts a clue scroll."""
        if ctx.channel.id == COMBAT_CHANNEL:
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

    @commands.group(invoke_without_command=True)
    async def shop(self, ctx):
        """Shows the items available at the shop."""
        if ctx.channel.id == SHOP_CHANNEL:
            messages = items.print_shop(ctx.author.id)
            for message in messages:
                await ctx.send(message)

    @shop.command(name='buy')
    async def _buy(self, ctx, *args):
        """Buys something from the shop."""
        item = ' '.join(args)
        if ctx.channel.id == SHOP_CHANNEL:
            out = items.buy(ctx.author.id, item, 1)
            await ctx.send(out)

    @shop.command(name='sell')
    async def _sell(self, ctx, *args):
        """Sells the player's inventory for GasterCoin."""
        if ctx.channel.id == SHOP_CHANNEL:
            try:
                number = int(args[0])
                item = ' '.join(args[1:])
            except ValueError:
                number = 1
                item = ' '.join(args)
            out = items.sell(ctx.author.id, item, number=number)
            await ctx.send(out)

    @shop.command(name='sellall')
    async def _sellall(self, ctx, maxvalue=None):
        """Sells all items in the player's inventory (below a certain value) for GasterCoin."""
        if ctx.channel.id == SHOP_CHANNEL:
            inventory = users.read_user(ctx.author.id)
            if maxvalue is None:
                value = users.get_value_of_inventory(inventory)
                ac.update_account(ctx.author.id, value)
                users.clear_inventory(ctx.author.id)
            else:
                value = users.get_value_of_inventory(inventory, under=maxvalue)
                ac.update_account(ctx.author.id, value)
                users.clear_inventory(ctx.author.id, under=maxvalue)
            value_formatted = '{:,}'.format(value)
            maxvalue_formatted = '{:,}'.format(int(maxvalue))
            await ctx.send(f"All items in {ctx.author.name}'s inventory worth under G${maxvalue_formatted} "
                           f"sold for G${value_formatted}!")

    @shop.command(name='trade')
    async def _trade(self, ctx, *args):
        """Trades to a person a number of a given object for a given price."""
        if ctx.channel.id == SHOP_CHANNEL:
            if len(args) < 4:
                await ctx.send('Error: args missing. Syntax is `~shop trade [name] [number] [item] [offer]`.')
                return

            name = args[0]
            for member in ctx.guild.members:
                if name.lower() in member.name.lower():
                    name_member = member
                    break
            else:
                await ctx.send(f'Error: {name} not found in server.')
                return

            try:
                number = int(args[1])
            except ValueError:
                await ctx.send(f'Error {args[1]} is not a valid number.')
                return

            try:
                offer = ac.parse_int(args[-1])
                itemid = items.find_by_name(' '.join(args[2:-1]))
            except ValueError:
                await ctx.send(f'Error {args[-1]} is not a valid offer.')
                return
            except KeyError:
                await ctx.send(f"Error: {' '.join(args[2:-1])} is not a valid item.")
                return

            if not users.item_in_inventory(ctx.author.id, itemid, number):
                await ctx.send(f'Error: you do not have {number} {items.add_plural(itemid)} in your inventory.')
                return

            if not items.is_tradable(itemid):
                await ctx.send(f'Error: you can not trade this item. ({items.get_attr(itemid)})')
                return

            out = ac.check_if_valid_transaction(name_member.id, offer)
            if out != ac.SUCCESS_STRING:
                await ctx.send(out)
                return

            offer_formatted = '{:,}'.format(offer)
            out = f'{items.SHOP_HEADER}{ctx.author.name.title()} wants to sell {name_member.mention} {number} ' \
                  f'{items.add_plural(itemid)} for G${offer_formatted}. To accept this offer, reply ' \
                  f'to this post with a :thumbsup:. Otherwise, this offer will expire in one minute.'
            msg = await ctx.send(out)
            await msg.add_reaction('\N{THUMBS UP SIGN}')

            while True:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=60)
                    if str(reaction.emoji) == '👍' and user == name_member and reaction.message.id == msg.id:
                        ac.update_account(name_member.id, -offer)
                        ac.update_account(ctx.author.id, offer)
                        loot = number * [itemid]
                        users.update_inventory(ctx.author.id, loot, remove=True)
                        users.update_inventory(name_member.id, loot)
                        await ctx.send(f'{items.SHOP_HEADER}{ctx.author.name.title()} successfully sold {number} '
                                       f'{items.add_plural(itemid)} to {name_member.name} for G${offer_formatted}!')
                        return
                except asyncio.TimeoutError:
                    await msg.edit(content=f'One minute has passed and your offer has been cancelled.')
                    return

    @commands.group(invoke_without_command=True, aliases=['quest'])
    async def quests(self, ctx, questid=None):
        if ctx.channel.id == COMBAT_CHANNEL:
            if questid is not None:
                out = quests.print_details(ctx.author.id, questid)
            else:
                out = quests.print_list(ctx.author.id)
            await ctx.send(out)

    @quests.command(name='start')
    async def _start(self, ctx, questid):
        """lets a user start a quest."""
        if ctx.channel.id == COMBAT_CHANNEL:
            out = quests.start_quest(ctx.author.id, questid)
            await ctx.send(out)

    @commands.command()
    async def gather(self, ctx, *args):
        """Gathers items."""
        if ctx.channel.id == COMBAT_CHANNEL:
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
        if ctx.channel.id == BANK_CHANNEL:
            messages = craft.print_list(ctx.author.id)
            for message in messages:
                await ctx.send(message)

    @recipes.command(name='info')
    async def _info(self, ctx, *args):
        """Lists the details of a particular recipe."""
        if ctx.channel.id == BANK_CHANNEL:
            recipe = ' '.join(args)
            out = craft.print_recipe(ctx.author.id, recipe)
            await ctx.send(out)

    @recipes.command(name='craft')
    async def _craft(self, ctx, *args):
        if ctx.channel.id == BANK_CHANNEL:
            try:
                number = int(args[0])
                recipe = ' '.join(args[1:])
            except ValueError:
                number = 1
                recipe = ' '.join(args)
            out = craft.craft(ctx.author.id, recipe, n=number)
            await ctx.send(out)

    async def check_adventures(self):
        """Check if any actions are complete and notifies the user if they are done."""
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            finished_tasks = adv.get_finished()
            for task in finished_tasks:
                with open('./subs/miniscape/resources/finished_tasks.txt', 'a+') as f:
                    f.write(';'.join(task) + '\n')
                adventureid, userid = int(task[0]), int(task[1])
                bot_self = self.bot.get_guild(config.guild_id).get_channel(471440571207254017)
                person = self.bot.get_guild(config.guild_id).get_member(int(userid))
                adventures = {
                    0: slayer.get_result,
                    1: slayer.get_kill_result,
                    2: quests.get_result,
                    3: craft.get_gather,
                    4: clues.get_clue_scroll
                }
                out = adventures[adventureid](person, task[3:])
                await bot_self.send(out)
            await asyncio.sleep(60)


def setup(bot):
    """Adds the cog to the bot."""
    bot.add_cog(Miniscape(bot))
