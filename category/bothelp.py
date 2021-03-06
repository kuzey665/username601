import discord
from discord.ext import commands
import sys
import requests
from json import loads
from os import getcwd, name, environ
sys.path.append(environ['BOT_MODULES_DIR'])
from decorators import command, cooldown
from datetime import datetime as t
# import selfDB, Dashboard

class bothelp(commands.Cog):
    def __init__(self, client):
        self._categories = "\n".join([f"{i + 2}. `{client.cmds.categories[i]}`" for i in range(len(client.cmds.categories))])
        self._init_help = [discord.Embed(title="The bot help embed™️", description="Use the reactions to move to the next page.\n\n**PAGES:**\n1. `This page`\n"+self._categories)]
        
    @command('supportserver,support-server,botserver,bot-server')
    @cooldown(2)
    async def support(self, ctx):
        return await ctx.send(ctx.bot.utils.config('SERVER_INVITE'))

    @command('subscribe,dev,development,devupdates,dev-updates,development-updates')
    @cooldown(5)
    async def sub(self, ctx, *args):
        if len(args)==0 or 'help' in ''.join(args).lower():
            embed = discord.Embed(title='Get development updates and/or events in your server!', description='Want to get up-to-date development updates? either it is bugfixes, cool events, etc.\nHow do you set up? Use `{}sub <discord webhook url>`.\nIf you still do not understand, [please watch the tutorial video here.](https://vierofernando.is-inside.me/fEhT86EE.mp4)'.format(ctx.bot.command_prefix), color=ctx.guild.me.roles[::-1][0].color)
            return await ctx.send(embed=embed)
        elif 'reset' in ''.join(args).lower():
            ctx.bot.db.Dashboard.subscribe(None, ctx.guild.id, reset=True)
            return await ctx.send('{} | Subscription has been deleted.'.format(ctx.bot.success_emoji))
        url = args[0].replace('<', '').replace('>', '')
        try:
            web = discord.Webhook.from_url(
                url,
                adapter=discord.RequestsWebhookAdapter()
            )
        except: raise ctx.bot.utils.send_error_message("Invalid Webhook URL. Please send the one according to the tutorial.")
        ctx.bot.db.Dashboard.subscribe(url, ctx.guild.id)
        await ctx.message.add_reaction(ctx.bot.success_emoji)
        web.send(
            embed=discord.Embed(title=f'Congratulations, {str(ctx.author)}!', description='Your webhook is now set! ;)\nNow every development updates or username601 events will be set here.\n\nIf you change your mind, you can do `{}sub reset` to remove the webhook from the database.\n[Join our support server if you still have any questions.]({})'.format(ctx.bot.command_prefix, ctx.bot.utils.config('SERVER_INVITE')), color=discord.Color.green()),
            username='Username601 News',
            avatar_url=ctx.bot.user.avatar_url
        )

    @command('commands,yardim,yardım')
    @cooldown(2)
    async def help(self, ctx, *args):
        if len(args) == 0:
            embeds = self._init_help
            for category in ctx.bot.cmds.categories:
                embed = discord.Embed(title=category, description="**Commands:**```"+(", ".join([command['name'] for command in ctx.bot.cmds.get_commands_from_category(category.lower())]))+"```")
                embed.set_footer(text=f"Type `{ctx.bot.command_prefix}help <command>` to view command in a detailed version.")
                embeds.append(embed)
            
            paginator = ctx.bot.EmbedPaginator(ctx, embeds, show_page_count=True, auto_set_color=True)
            return await paginator.execute()
        
        data = ctx.bot.cmds.query(' '.join(args).lower())
        if data is None: raise ctx.bot.utils.send_error_message("Your command/category name does not exist, sorry!")
        
        embed = ctx.bot.ChooseEmbed(ctx, data, key=(lambda x: "[`"+x["type"]+"`] `"+x["name"]+"`"))
        result = await embed.run()
        
        if result is None: return
        is_command = (result["type"] == "COMMAND")
        data = ctx.bot.cmds.get_command_info(result["name"].lower()) if is_command else ctx.bot.cmds.get_commands_from_category(result["name"].lower())
        
        desc = '**Command name: **{}\n**Function: **{}\n**Category: **{}'.format(
            data['name'], data['function'], data['category']
        ) if is_command else '**Commands count: **{}\n**Commands:**```{}```'.format(len(data), ', '.join([i['name'] for i in data]))
        embed = ctx.bot.Embed(ctx, title="Help for "+result["type"].lower()+": "+result["name"], desc=desc)
        if is_command:
            parameters = 'No parameters required.' if len(data['parameters'])==0 else '\n'.join([i for i in data['parameters']])
            apis = 'No APIs used.' if len(data['apis'])==0 else '\n'.join(map(lambda x: f"[{x}]({x})", data['apis']))
            embed.fields = {
                'Parameters': parameters,
                'APIs used': apis
            }
        return await embed.send()

    @command()
    @cooldown(2)
    async def vote(self, ctx):
        embed = discord.Embed(title='Support by Voting us at top.gg!', description='Sure thing, mate! [Vote us at top.gg by clicking me!](https://top.gg/bot/'+str(ctx.bot.user.id)+'/vote)', colour=ctx.guild.me.roles[::-1][0].color)
        await ctx.send(embed=embed)
    
    @command('sourcecode,source-code,git,repo')
    @cooldown(2)
    async def github(self, ctx):
        embed = discord.Embed(title="Click me to visit the Bot's github page.", colour=ctx.guild.me.roles[::-1][0].color, url=ctx.bot.utils.config('GITHUB_REPO'))
        await ctx.send(embed=embed)
    
    @command('inviteme,invitelink,botinvite,invitebot,addtoserver,addbot')
    @cooldown(2)
    async def invite(self, ctx):
        embed = discord.Embed(
            title='Sure thing! Invite this bot to your server by clicking me.',
            url='https://discord.com/api/oauth2/authorize?client_id='+str(ctx.bot.user.id)+'&permissions=8&scope=bot',
            colour=ctx.guild.me.roles[::-1][0].color
        )
        await ctx.send(embed=embed)
    
    @command('report,suggest,bug,reportbug,bugreport')
    @cooldown(15)
    async def feedback(self, ctx, *args):
        if ((len(args)==0) or (len(''.join(args))>1000)): raise ctx.bot.utils.send_error_message("Invalid feedback length.")
        elif (('discord.gg/' in ' '.join(args)) or ('discord.com/invite/' in ' '.join(args))): raise ctx.bot.utils.send_error_message("Please do NOT send invites. This is NOT advertising.")
        else:
            wait = await ctx.send(ctx.bot.loading_emoji + ' | Please wait... Transmitting data to owner...')
            banned = ctx.bot.db.selfDB.is_banned(ctx.author.id)
            if not banned:
                try:
                    fb = ' '.join(args)
                    feedbackCh = ctx.bot.get_channel(ctx.bot.utils.config('FEEDBACK_CHANNEL', integer=True))
                    await feedbackCh.send('<@'+ctx.bot.utils.config('OWNER_ID')+'>, User with ID: '+str(ctx.author.id)+' sent a feedback: **"'+str(fb)+'"**')
                    embed = discord.Embed(title='Feedback Successful', description=ctx.bot.success_emoji + '** | Success!**\nThanks for the feedback!\n**We will DM you as the response. **If you are unsatisfied, [Join our support server and give us more details.]('+ctx.bot.utils.config('SERVER_INVITE')+')',colour=ctx.guild.me.roles[::-1][0].color)
                    await wait.edit(content='', embed=embed)
                except:
                    raise ctx.bot.utils.send_error_message('There was an error while sending your feedback. Sorry! :(')
            else:
                raise ctx.bot.utils.send_error_message(f"You have been banned from using the Feedback command.\nReason: {str(banned)}")
                
    @command()
    @cooldown(2)
    async def ping(self, ctx):
        msgping = str(round((t.now().timestamp() - ctx.message.created_at.timestamp())*1000))
        wait = await ctx.send('pinging...')
        dbping, extras = ctx.bot.db.selfDB.ping(), ''
        wsping = str(round(ctx.bot.ws.latency*1000))
        embed = discord.Embed(title=f'Pong!', description=f'**Message latency: **{msgping} ms.\n**Client Latency:** {wsping} ms.\n**Database latency:** {dbping} ms.', colour=ctx.guild.me.roles[::-1][0].color)
        embed.set_thumbnail(url='https://i.pinimg.com/originals/21/02/a1/2102a19ea556e1d1c54f40a3eda0d775.gif')
        await wait.edit(content='', embed=embed)
    
    @command('botstats,meta')
    @cooldown(10)
    async def stats(self, ctx):
        bot_uptime = ctx.bot.utils.lapsed_time_from_seconds(round(t.now().timestamp() - ctx.bot.last_downtime))
        embed = discord.Embed(description='This bot is serving **{} servers** each with **{} users.**\nBot uptime: {}\nOS uptime: {}\nLast downtime: {} UTC\nCommands run in the past {}: {}\nTotal commands: {}'.format(
            len(ctx.bot.guilds),
            len(ctx.bot.users),
            bot_uptime,
            ctx.bot.utils.run_terminal('uptime -p')[3:],
            t.fromtimestamp(ctx.bot.last_downtime),
            bot_uptime,
            ctx.bot.command_uses,
            ctx.bot.cmds.length
        ), color=ctx.guild.me.roles[::-1][0].color)
        await ctx.send(embed=embed)

def setup(client):
    client.add_cog(bothelp(client))
