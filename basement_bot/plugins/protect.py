import cogs
import munch


def setup(bot):
    bot.add_cog(Protector(bot))


class Protector(cogs.MatchPlugin, cogs.HttpPlugin):

    PLUGIN_NAME = __name__
    ALERT_ICON_URL = "https://cdn.icon-icons.com/icons2/2063/PNG/512/alert_danger_warning_notification_icon_124692.png"
    PASTEBIN_URL = "https://pastebin.com/api/api_post.php"

    async def preconfig(self):
        self.string_map = {
            keyword: munch.munchify(filter_config)
            for keyword, filter_config in self.config.string_map.items()
        }

    async def match(self, ctx, content):
        if not ctx.channel.id in self.config.included_channels:
            return False

        # admin = await self.bot.is_bot_admin(ctx)
        # if admin:
        #     return False

        # extend alerts here
        ctx.protect_actions = munch.Munch()
        ctx.protect_actions.string_alert = None
        ctx.protect_actions.length_alert = None

        if len(content) > self.config.length_limit:
            ctx.protect_actions.length_alert = True
            return True

        for keyword, filter_config in self.string_map.items():
            # make a copy because we might modify it
            search_keyword = keyword
            search_content = content
            if filter_config.sensitive:
                search_keyword = search_keyword.lower()
                search_content = search_content.lower()

            if search_keyword in search_content:
                filter_config["trigger"] = keyword
                ctx.protect_actions.string_alert = filter_config
                return True

    async def response(self, ctx, content):
        if ctx.protect_actions.length_alert:
            await self.handle_length_alert(ctx, content)
        elif ctx.protect_actions.string_alert:
            await self.handle_string_alert(ctx, content)

    async def handle_string_alert(self, ctx, content):
        if ctx.protect_actions.string_alert.delete:
            alert_message = f"I deleted your message because: {ctx.protect_actions.string_alert.message}. Check your DM's for the original message"
            await ctx.message.delete()
            await self.send_original_message(ctx, content)
        else:
            alert_message = ctx.protect_actions.string_alert.message

        await self.bot.h.tagged_response(ctx, alert_message)
        await self.send_admin_alert(
            ctx,
            f"Message contained trigger: `{ctx.protect_actions.string_alert.trigger}`",
        )

    async def handle_length_alert(self, ctx, content):
        await ctx.message.delete()

        pastebin_link = await self.create_pastebin_link(
            f"Paste by {ctx.message.author.display_name}", content
        )
        if pastebin_link:
            await self.bot.h.tagged_response(
                ctx,
                f"I put your message on Pastebin because it was longer than {self.config.length_limit} characters: {pastebin_link}",
            )
        else:
            await self.bot.h.tagged_response(
                ctx,
                f"I deleted your message because it was longer than {self.config.length_limit} characters; please read our #rules. Check your DM's for the original message",
            )
            await ctx.author.send(f"Deleted message: ```{content[:1994]}```")

    async def send_admin_alert(self, ctx, message):
        alert_channel = self.bot.get_channel(self.config.alert_channel)
        if not alert_channel:
            return

        embed = self.bot.embed_api.Embed(
            title="Protect Plugin Alert", description=f"{message}"
        )

        embed.add_field(name="User", value=ctx.author.mention)

        embed.add_field(name="Channel", value=f"#{ctx.channel.name}")

        embed.add_field(name="Message", value=ctx.message.content, inline=False)

        embed.set_thumbnail(url=self.ALERT_ICON_URL)

        await alert_channel.send(embed=embed)

    async def create_pastebin_link(self, title, content):
        if not self.config.pastebin_api_key or not content:
            return None

        data = {
            "api_dev_key": self.config.pastebin_api_key,
            "api_option": "paste",
            "api_paste_name": title,
            "api_paste_code": content,
        }

        response = await self.http_call(
            "post", self.PASTEBIN_URL, data=data, get_raw_response=True
        )
        return response.text
