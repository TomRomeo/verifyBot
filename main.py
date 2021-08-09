import discord
from discord.ext import commands
import logging # logging module for discord.py
from dotenv import load_dotenv
import os
from claptcha import Claptcha
import asyncio
import random
import string
from PIL import Image

# TODO: some logic for production / debugging
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

load_dotenv() # take environment variables from .env

def randomString():
    rndLetters = (random.choice(string.ascii_uppercase) for _ in range(6))
    return "".join(rndLetters)

class VerifylyBot(commands.Bot):

    memberRole = 724132070695370763
    verifyChannel = 874263657788350464
    usersWaitingFor = []

    async def on_ready(self):
        print("Bot started ({})".format(self.user))
        print("---------------")
        print("On following servers:")
        for server in self.guilds:
            print(server)
        print("---------------")



    def __init__(self, command_prefix, self_bot):
        commands.Bot.__init__(self, command_prefix=command_prefix, self_bot=self_bot)


        @self.command()
        async def verify(ctx):

            # check if channel is verify channel and user doesn't have member role
            if ctx.channel.id == self.verifyChannel:

                if self.memberRole not in [x.id for x in ctx.author.roles]:

                    if ctx.author.id in self.usersWaitingFor:
                        await ctx.send(embed=discord.Embed(color=discord.Color.red(), title="Nono", description="You already have an active captcha"))
                        return


                    await ctx.message.delete()

                    self.usersWaitingFor.append(ctx.author.id)

                    # create dm thread
                    channel = await ctx.author.create_dm()

                    # Initialize Claptcha object with random text and DejaVuSans as font
                    c = Claptcha(randomString, "/usr/share/fonts/dejavu/DejaVuSansMono.ttf",
                    resample=Image.BICUBIC, noise=0.3)
                    
                    # Get PIL Image object
                    text, image = c.bytes
                    print(text)
                    
                    file = discord.File(image, filename="image.png")
                    emb = discord.Embed(title="Type in the captcha text")
                    emb.set_image(url='attachment://image.png')
                    await channel.send(file=file, embed=emb)


                    def checkIfMessageFromAuthor(message):
                        if isinstance(message.channel, discord.channel.DMChannel) and message.author == ctx.author:
                            return True
                        return False

                    try:
                        reply = await self.wait_for('message', timeout=300, check=checkIfMessageFromAuthor)

                        # if the user types the correct captcha
                        if reply.content == text:
                            await ctx.author.add_roles(ctx.channel.guild.get_role(self.memberRole))
                            await channel.send(embed=discord.Embed(color=discord.Color.green(), title="Great!", description="You have been verified!"))
                        else:
                            await channel.send(embed=discord.Embed(color=discord.Color.red(), title="Nono", description="You entered a wrong captcha.\nTo try again, type {}verify in the verification channel again".format(self.command_prefix)))

                        self.usersWaitingFor.remove(ctx.author.id)


                    except asyncio.TimeoutError:
                        self.usersWaitingFor.remove(ctx.author.id)
                        return

                else:
                    await ctx.send(embed=discord.Embed(color=discord.Color.red(), title="Nono", description="You already have the member role"))





bot = VerifylyBot(command_prefix="!", self_bot=False)

bot.run(os.getenv('BOT_TOKEN'))
