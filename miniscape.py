"""TODO FIX THIS."""
import asyncio
import config
import discord
from discord.ext import commands

from subs.gastercoin import account as ac

from subs.miniscape import monsters as mon
from subs.miniscape import items
from subs.miniscape import users
from subs.miniscape import quests
from subs.miniscape import adventures as adv
from subs.miniscape import slayer

from subs.miniscape.files import CREATOR_ID

RESOURCES_DIRECTORY = f'./subs/miniscape/resources/'

PERMISSION_ERROR_STRING = f'Error: You do not have permission to use this command.'

COMBAT_CHANNEL = 471440571207254017
BANK_CHANNEL = 471440651620319233
SHOP_CHANNEL = 471445748995850240


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

    # @slayer.command(name='cancel')
    # async def _cancel(self, ctx):
    #     try:
    #         task = slayer.get_task_info(ctx.author.id)
    #     except ValueError:
    #         await ctx.send('You do not currently have a slayer task. You can get one by typing `~slayer`')
    #         return
    #     num_to_kill = task[2]
    #     monster_name = task[1]
    #     time_left = task[-1]
    #     cancel_fee = 500000
    #     fee_formatted = '{:,}'.format(cancel_fee)
    #     out = f'Would you like to cancel your task of {num_to_kill} {monster_name}? ' \
    #           f'If you do, react with a :thumbsup:. However, it will cost G${fee_formatted}. '\
    #           f'Otherwise, you can get a new task in {time_left} minutes.'
    #     msg = await ctx.send(out)
    #     await msg.add_reaction('\N{THUMBS UP SIGN}')
    #     while True:
    #         try:
    #             reaction, user = await self.bot.wait_for('reaction_add', timeout=60)
    #             if str(reaction.emoji) == '👍' and user == ctx.author:
    #                 out = ac.check_if_valid_transaction(ctx.author.id, cancel_fee)
    #                 if out == ac.SUCCESS_STRING:
    #                     ac.update_account(ctx.author.id, -cancel_fee)
    #                     slayer.remove_task_from_file(ctx.author.id)
    #                     await msg.edit(content=f"{ctx.author.name}'s slayer task has been cancelled. "
    #                                            f"You are now free to accept another task.")
    #                     break
    #                 else:
    #                     await msg.edit(content=out)
    #         except asyncio.TimeoutError:
    #             await msg.edit(content=f'One minute has passed. If you still wish to cancel your task, please type '\
    #                                    f'`~slayer cancel` again.')
    #             break

    @commands.group(aliases=['invent', 'inventory', 'item'], invoke_without_command=True)
    async def items(self, ctx, search=''):
        """Show's the player's inventory."""
        if ctx.channel.id == BANK_CHANNEL:
            inventory = users.print_inventory(ctx.author.id, search.lower())
            for message in inventory:
                await ctx.send(message)

    @items.command(name='stats', aliases=['stat'])
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

    @kill.command(name='cancel')
    async def _cancel(self, ctx):
        """Cancels the user's kill."""
        if ctx.channel.id == COMBAT_CHANNEL:
            adv.remove(ctx.author.id)
            await ctx.send('Your kill has been removed.')

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
    async def compare(self, ctx, item1, item2):
        """Compares the stats of two items."""
        if ctx.channel.id == BANK_CHANNEL:
            out = items.compare(item1.lower(), item2.lower())
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

    # @quest.command(name='cancel')
    # async def _cancel(self, ctx):
    #     """Cancels the user's quest."""
    #     if ctx.channel.id == COMBAT_CHANNEL:
    #         adv.remove(ctx.author.id)
    #         await ctx.send('Your quest has been cancelled.')

    @commands.command()
    async def cancel(self, ctx):
        await ctx.send('soon:tm:')

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
                    2: quests.get_result
                }
                out = adventures[adventureid](person, task[3:])
                await bot_self.send(out)
            await asyncio.sleep(60)


def setup(bot):
    """Adds the cog to the bot."""
    bot.add_cog(Miniscape(bot))
