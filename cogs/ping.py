import asyncio
import socket
import contextlib
from urllib.parse import urlparse

import discord
from discord.ext import commands

from utils import handle_rate_limit


class Ping(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping_site(self, ctx: commands.Context, *, target: str):
        """
        Checks if a host is reachable and shows its IP/latency.

        Usage:
          !ping example.com
          !ping https://example.com
          !ping example.com:8080
        """
        if not await handle_rate_limit(ctx):
            return

        raw_input = target.strip()

        # Normalise to a URL so urlparse works
        if not raw_input.startswith(("http://", "https://")):
            url = "https://" + raw_input
        else:
            url = raw_input

        parsed = urlparse(url)

        host = parsed.hostname
        port = parsed.port

        # Default ports if none provided
        if port is None:
            if parsed.scheme == "http":
                port = 80
            else:
                port = 443

        if not host:
            await ctx.send("Could not parse a valid hostname from your input.")
            return

        await ctx.send(f"🔍 Resolving and pinging `{host}` (port {port})...")
        print(f"-> Received !ping request for: {raw_input} -> host={host}, port={port}")

        try:
            # Resolve hostname to IP (first IPv4/IPv6 result)
            loop = asyncio.get_running_loop()
            addrinfo = await loop.getaddrinfo(
                host,
                port,
                type=socket.SOCK_STREAM,
            )

            if not addrinfo:
                await ctx.send(f"❌ Could not resolve hostname `{host}`.")
                return

            family, socktype, proto, canonname, sockaddr = addrinfo[0]
            ip_address, resolved_port = sockaddr[0], sockaddr[1]

        except socket.gaierror as e:
            print(e)
            await ctx.send(f"❌ DNS resolution failed for `{host}`")
            return
        except Exception as e:
            print(e)
            await ctx.send(f"❌ Unexpected error while resolving `{host}`")
            return

        # Try to open a TCP connection as a "ping"
        try:
            start = loop.time()

            connect_coro = asyncio.open_connection(ip_address, port)
            reader, writer = await asyncio.wait_for(connect_coro, timeout=5.0)

            latency_ms = (loop.time() - start) * 1000

            # Cleanly close connection
            writer.close()
            with contextlib.suppress(Exception):
                await writer.wait_closed()

            msg_lines = [
                f"✅ Host **UP**",
                f"- Hostname: `{host}`",
                f"- IP: `{ip_address}`",
                f"- Port: `{port}`",
                f"- Latency: `{latency_ms:.1f} ms` (TCP connect)",
            ]

            await ctx.send("\n".join(msg_lines))

        except asyncio.TimeoutError:
            await ctx.send(
                f"❌ `{host}` ({ip_address}:{port}) appears to be **DOWN** or not accepting TCP connections.\n"
                f"- Reason: connection **timed out** after 5 seconds."
            )
        except (ConnectionRefusedError, OSError) as e:
            print(e)
            await ctx.send(
                f"⚠️ `{host}` resolved to `{ip_address}`, but the TCP connection failed.\n"
            )
        except Exception as e:
            print(e)
            await ctx.send(
                f"❌ Unexpected error while pinging `{host}` ({ip_address}:{port}).\n"
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Ping(bot))
