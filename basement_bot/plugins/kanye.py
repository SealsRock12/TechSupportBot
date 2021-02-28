import asyncio
import random

import cogs


def setup(bot):
    config = bot.PluginConfig()
    config.add(
        key="channel",
        datatype="int",
        title="DuckHunt Channel ID",
        description="The ID of the channel the Kanye West quote should appear in",
        default=None,
    )
    config.add(
        key="min_wait",
        datatype="int",
        title="Min wait (hours)",
        description="The minimum number of hours to wait between Kanye events",
        default=24,
    )
    config.add(
        key="max_wait",
        datatype="int",
        title="Max wait (hours)",
        description="The minimum number of hours to wait between Kanye events",
        default=48,
    )

    return bot.process_plugin_setup(cogs=[KanyeQuotes], config=config)

class KanyeQuotes(cogs.LoopCog):

    API_URL = "https://api.kanye.rest"
    KANYE_PICS = [
        "https://i.imgur.com/ITmTXGz.jpg",
        "https://i.imgur.com/o8BkPrL.jpg",
        "https://i.imgur.com/sA5qP3F.jpg",
        "https://i.imgur.com/1fX29Y3.jpg",
        "https://i.imgur.com/g1o2Gro.jpg",
    ]

    async def execute(self, config, _):
        response = await self.bot.http_call("get", self.API_URL)

        quote = response.get("quote")
        if not quote:
            return

        embed = self.bot.embed_api.Embed(title=f'"{quote}"', description="Kanye Quest")

        embed.set_thumbnail(url=random.choice(self.KANYE_PICS))

        channel = self.bot.get_channel(int(config.channel.value))
        if not channel:
            return

        await channel.send(embed=embed)

    async def wait(self, config, _):
        await asyncio.sleep(
            random.randint(
                config.min_hours * 3600,
                config.max_hours * 3600,
            )
        )
