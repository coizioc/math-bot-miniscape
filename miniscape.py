"""Implements commands related to running a freemium-style text-based RPG."""
import asyncio

from discord.ext import commands

import config
from subs.gastercoin import account as ac
from subs.miniscape import adventures as adv
from subs.miniscape import items
from subs.miniscape import monsters as mon
from subs.miniscape import quests
from subs.miniscape import craft
from subs.miniscape import slayer
from subs.miniscape import users

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

    @commands.group(aliases=['invent', 'inventory', 'item'], invoke_without_command=True)
    async def items(self, ctx, search=''):
        """Show's the player's inventory."""
        if ctx.channel.id == BANK_CHANNEL:
            inventory = users.print_inventory(ctx.author.id, search.lower())
            for message in inventory:
                await ctx.send(message)

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
                if args[0].isdigit():
                    number = args[0]
                    monster = ' '.join(args[1:])
                    out = slayer.get_kill(ctx.author.id, monster, number=number)
                elif args[-1].isdigit():
                    length = args[-1]
                    monster = ' '.join(args[:-1])
                    out = slayer.get_kill(ctx.author.id, monster, length=length)
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

    @commands.command()
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
        out = slayer.print_chance(ctx.author.id, monsterid, monster_dam=int(dam), monster_acc=int(acc),
                                  monster_arm=int(arm), monster_combat=int(cb), xp=int(xp), number=int(num),
                                  dragonfire=bool(dfire))
        await ctx.send(out)

    @commands.command()
    async def cancel(self, ctx):
        """Cancels your current action."""
        try:
            task = adv.get_adventure(ctx.author.id)

            adventureid = task[0]
            if adventureid == '0':
                if users.item_in_inventory(ctx.author.id, '291', '1'):
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
                out = 'You are not currently doing anything.'
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
    async def _sell(self, ctx, item, number=None):
        """Sells the player's inventory for GasterCoin."""
        if ctx.channel.id == SHOP_CHANNEL:
            if item != 'all':
                if number is None:
                    number = 1
                out = items.sell(ctx.author.id, item, number=None)
                await ctx.send(out)
            else:
                inventory = users.read_user(ctx.author.id)
                if number is None:
                    value = users.get_value_of_inventory(inventory)
                    ac.update_account(ctx.author.id, value)
                    users.clear_inventory(ctx.author.id)
                else:
                    value = users.get_value_of_inventory(inventory, under=number)
                    ac.update_account(ctx.author.id, value)
                    users.clear_inventory(ctx.author.id, under=number)
                value_formatted = '{:,}'.format(value)
                await ctx.send(f"{ctx.author.name}'s inventory sold for G${value_formatted}")

    @commands.group(invoke_without_command=True, aliases=['quests'])
    async def quest(self, ctx, questid=None):
        if ctx.channel.id == COMBAT_CHANNEL:
            if questid is not None:
                out = quests.print_details(ctx.author.id, questid)
            else:
                out = quests.print_list(ctx.author.id)
            await ctx.send(out)

    @quest.command(name='start')
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
            out = craft.print_recipe(recipe)
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
                adventureid, userid = int(task[0]), int(task[1])
                bot_self = self.bot.get_guild(config.guild_id).get_channel(471440571207254017)
                person = self.bot.get_guild(config.guild_id).get_member(int(userid))
                adventures = {
                    0: slayer.get_result,
                    1: slayer.get_kill_result,
                    2: quests.get_result,
                    3: craft.get_gather
                }
                out = adventures[adventureid](person, task[3:])
                await bot_self.send(out)
            await asyncio.sleep(60)


def setup(bot):
    """Adds the cog to the bot."""
    bot.add_cog(Miniscape(bot))
