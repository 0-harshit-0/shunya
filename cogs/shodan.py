import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
import shodan

from utils.rate_limit import handle_rate_limit

# --- Configuration ---
load_dotenv()
SHODAN_API_KEY = os.getenv("SHODAN_API_KEY")


class ShodanCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.shodan = shodan.Shodan(SHODAN_API_KEY) if SHODAN_API_KEY else None

    @commands.hybrid_command(name="shodan")
    async def shodan_search(self, ctx: commands.Context, *, query: str):
        limit = 5
        """
        Search Shodan for internet-facing devices matching a query.

        Usage:
          /shodan apache country:US
          /shodan 10 nginx port:80
        Where "10" is the max number of results (1–20).
        """
        if not await handle_rate_limit(ctx):
            return

        if not self.shodan:
            await ctx.send("Shodan API key is not configured on the bot.")
            return

        if limit < 1 or limit > 20:
            await ctx.send("Please provide a result limit between 1 and 20.")
            return

        if len(query) > 200:
            await ctx.send("Please use a shorter query (max 200 characters).")
            return

        print(f"-> Received /shodan request: limit={limit}, query={query}")

        try:
            async with ctx.typing():
                loop = asyncio.get_running_loop()
                results = await loop.run_in_executor(
                    None,
                    lambda: self.shodan.search(query, limit=limit)
                )

            total = results.get("total", 0)
            matches = results.get("matches", [])

            if not matches:
                await ctx.send(f"No Shodan results for `{query}`.")
                return

            # Header
            lines = [
                f"## Shodan search results",
                f"Query: `{query}`",
                f"Showing {len(matches)} of ~{total:,} matches.",
                "",
            ]

            for idx, match in enumerate(matches, start=1):
                ip_str = match.get("ip_str", "unknown IP")
                port = match.get("port", "?")
                transport = match.get("transport")
                if transport:
                    transport = transport.upper()

                org = match.get("org") or "N/A"
                asn = match.get("asn") or "N/A"

                location = match.get("location") or {}
                country = location.get("country_name") or "N/A"
                city = location.get("city") or "Unknown city"

                os_name = match.get("os") or "Unknown OS"
                hostnames_list = match.get("hostnames") or []
                hostnames = ", ".join(hostnames_list[:3]) if hostnames_list else "None"

                product = match.get("product") or "Unknown service"
                version = match.get("version")
                product_str = product + (f" {version}" if version else "")

                tags_list = match.get("tags") or []
                tags = ", ".join(tags_list[:5]) if tags_list else "None"

                timestamp = (
                    match.get("timestamp")
                    or match.get("updated")
                    or "N/A"
                )

                vulns = match.get("vulns") or {}
                vuln_keys = list(vulns.keys())[:3] if isinstance(vulns, dict) else []
                vulns_str = ", ".join(vuln_keys) if vuln_keys else "None"

                banner = match.get("data") or ""
                banner_snippet = ""
                if banner:
                    first_line = banner.strip().splitlines()[0]
                    banner_snippet = first_line[:140]
                    banner_snippet = banner_snippet.replace("`", "´")

                # Per‑host block
                header_parts = [f"[{idx}] `{ip_str}:{port}`"]
                if transport:
                    header_parts.append(transport)
                header_line = " ".join(header_parts)

                lines.append(header_line)
                lines.append(f"- Service: {product_str}")
                lines.append(f"- Location: {city}, {country}")
                lines.append(f"- Org/ASN: {org} / {asn}")
                lines.append(f"- OS: {os_name}")
                lines.append(f"- Hostnames: {hostnames}")
                lines.append(f"- Tags: {tags}")
                lines.append(f"- Vulns: {vulns_str}")
                lines.append(f"- Last seen: {timestamp}")

                if banner_snippet:
                    lines.append(f"- Banner: `{banner_snippet}`")

                lines.append("")  # blank line between hosts

            message = "\n".join(lines)

            # Keep under Discord's 2000-character limit for a single message
            if len(message) > 2000:
                message = message[:1990] + "\n...(truncated)..."

            await ctx.send(message)

        except shodan.APIError as e:
            error_msg = str(e)
            print(f"[Shodan APIError] {error_msg}")

            if "Invalid API key" in error_msg:
                friendly = (
                    "Shodan reports the API key is invalid or has expired. "
                    "Please update SHODAN_API_KEY in the bot configuration."
                )
            elif "exceeded" in error_msg.lower() or "credits" in error_msg.lower():
                friendly = (
                    "Shodan query credits appear to be exhausted for this API key. "
                    "Check your Shodan account usage and plan."
                )
            else:
                friendly = f"Shodan API error: {error_msg}"

            await ctx.send(friendly)

        except Exception as e:
            print(f"[Shodan unexpected error] {type(e).__name__}: {e}")
            await ctx.send(
                "Unexpected error while querying Shodan. "
                "Check bot logs for details."
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(ShodanCog(bot))
