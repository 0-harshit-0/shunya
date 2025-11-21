import os
import discord
from discord.ext import commands
from utils.ai import generate_response
from dotenv import load_dotenv

load_dotenv()


class AutoReplyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if len(message.content) > 100:
            await message.channel.send(
                "Sorry, I can only respond to messages that are 100 characters or less! 😊"
            )
            return

        # Check triggers: bot mention or reply to bot
        if (
            self.bot.user in message.mentions
            or (
                message.reference
                and getattr(message.reference.resolved, "author", None) == self.bot.user
            )
        ):
            # Start building context
            context_parts = []

            # Include referenced message content if replying
            if message.reference and message.reference.resolved:
                context_parts.append(message.reference.resolved.content)

            # Find other mentioned users except bot itself and message author
            other_mentions = [user for user in message.mentions if user != self.bot.user]

            # For each mentioned user, fetch their last 3 messages from history
            for user in other_mentions:
                related_messages = []
                async for msg in message.channel.history(limit=100):
                    if msg.author == user and len(msg.content) <= 100:
                        related_messages.append(msg.content)
                        if len(related_messages) >= 3:
                            break
                # Add these messages in reverse chronological order to context
                if related_messages:
                    # Reverse so older messages come first
                    related_text = "\n".join(reversed(related_messages))
                    context_parts.append(f"Recent messages from {user.name}:\n{related_text}")

            # Combine all context parts and current message content for prompt
            full_context = "\n".join(context_parts) + "\n" + message.content

            prompt = os.getenv("REPLY_PROMPT") + full_context

            async with message.channel.typing():
                reply = await generate_response(prompt)

            await message.channel.send(reply)

async def setup(bot):
    await bot.add_cog(AutoReplyCog(bot))
