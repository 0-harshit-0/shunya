import os
import asyncio
import requests
from datetime import datetime
from dotenv import load_dotenv

import discord
from discord.ext import commands

from utils import handle_rate_limit  # assuming you have this from the Shodan cog

load_dotenv()

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
BASE_URL = "https://api.etherscan.io/v2/api"
CHAIN_ID = 1  # Ethereum mainnet


def fetch_latest_normal_txs(address: str, limit: int = 9):
    params = {
        "chainid": CHAIN_ID,
        "module": "account",
        "action": "txlist",
        "address": address,
        "startblock": 0,
        "endblock": 99999999,
        "page": 1,
        "offset": limit,
        "sort": "desc",
        "apikey": ETHERSCAN_API_KEY,
    }
    resp = requests.get(BASE_URL, params=params, timeout=10)
    data = resp.json()
    if data.get("status") != "1" or not isinstance(data.get("result"), list):
        print("Normal txs API problem:", data.get("message"), data.get("result"))
        return []
    return data["result"]


def fetch_latest_internal_txs(address: str, limit: int = 9):
    params = {
        "chainid": CHAIN_ID,
        "module": "account",
        "action": "txlistinternal",
        "address": address,
        "startblock": 0,
        "endblock": 99999999,
        "page": 1,
        "offset": limit,
        "sort": "desc",
        "apikey": ETHERSCAN_API_KEY,
    }
    resp = requests.get(BASE_URL, params=params, timeout=10)
    data = resp.json()
    if data.get("status") != "1" or not isinstance(data.get("result"), list):
        print("Internal txs API problem:", data.get("message"), data.get("result"))
        return []
    return data["result"]


def compare_txs_by_amount_and_timestamp(normal_txs, internal_txs, radius_seconds: int = 60):
    """
    Very simple heuristic: find pairs of normal/internal txs that:
      - have the same value (wei string), and
      - have timestamps within +/- radius_seconds.
    This *does not* guarantee a honeypot / trap, but may surface suspicious patterns.
    """
    internal_by_value = {}
    for itx in internal_txs:
        val = itx.get("value")
        internal_by_value.setdefault(val, []).append(itx)

    matched_pairs = []

    for ntx in normal_txs:
        val = ntx.get("value")
        if not val:
            continue

        candidates = internal_by_value.get(val, [])
        if not candidates:
            continue

        try:
            t_normal = int(ntx.get("timeStamp", "0"))
        except ValueError:
            continue

        for itx in candidates:
            try:
                t_internal = int(itx.get("timeStamp", "0"))
            except ValueError:
                continue

            if abs(t_normal - t_internal) <= radius_seconds:
                matched_pairs.append(
                    {
                        "normal": ntx,
                        "internal": itx,
                        "time_diff_seconds": abs(t_normal - t_internal),
                    }
                )

    return matched_pairs


class TrapCog(commands.Cog):
    """
    Cog providing a `!trap` command that inspects an Ethereum address' latest
    normal + internal transactions and reports simple suspicious patterns.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="trap")
    async def trap_command(self, ctx: commands.Context, address: str, limit: int = 9):
        """
        Check if an Ethereum address *might* be a trap/honeypot-like wallet
        by comparing recent normal and internal transactions.

        Usage:
          !trap 0xYourAddressHere
          !trap 0xYourAddressHere 5   # check last 5 normal/internal txs
        """
        if not await handle_rate_limit(ctx):
            return

        if not ETHERSCAN_API_KEY:
            await ctx.send("Etherscan API key is not configured on the bot.")
            return

        if not (1 <= limit <= 20):
            await ctx.send("Please provide a limit between 1 and 20.")
            return

        if not address.startswith("0x") or len(address) != 42:
            await ctx.send("Please provide a valid Ethereum address.") # (0x-prefixed, 42 chars)
            return

        print(f"-> Received /trap request: limit={limit}, address={address}")

        try:
            async with ctx.typing():
                loop = asyncio.get_running_loop()

                # Run blocking HTTP calls in executor
                normal_txs, internal_txs = await asyncio.gather(
                    loop.run_in_executor(None, fetch_latest_normal_txs, address, limit),
                    loop.run_in_executor(None, fetch_latest_internal_txs, address, limit),
                )

                matched_pairs = compare_txs_by_amount_and_timestamp(
                    normal_txs, internal_txs, radius_seconds=60
                )

            total_normal = len(normal_txs)
            total_internal = len(internal_txs)
            total_matches = len(matched_pairs)

            # --- NEW: simple trap heuristic ---
            trap_threshold = 3
            is_potential_trap = total_matches > trap_threshold

            lines = []
            lines.append("## Trap wallet heuristic check")
            lines.append(f"Address: `{address}`")
            # lines.append(
            #     f"Fetched {total_normal} normal txs and {total_internal} internal txs (latest, desc)."
            # )
            # lines.append(
            #     f"Found {total_matches} pairs where value matches and timestamps are within 60 seconds."
            # )
            lines.append("")

            if is_potential_trap:
                # Wallet looks suspicious under this heuristic
                lines.append(
                    "⚠️ This wallet shows multiple matching transaction pairs " #normal/internal
                    "with equal value and close timestamps."
                )
                lines.append(
                    "⚠️ It is **potentially a trap / honeypot-like wallet** under this simple heuristic."
                )
                lines.append(
                    "This is *not* definitive proof of a scam, but you should treat this address with extreme caution."
                )
                lines.append("")
            else:
                # Below threshold: not flagged, but still not guaranteed safe
                lines.append(
                    "No strong trap-like pattern detected by this specific heuristic "
                    # f"(≤ {trap_threshold} matching pairs)."
                )
                lines.append(
                    "⚠️ This does **not** guarantee the wallet is safe." #; it only means this pattern wasn't strongly observed.
                )
                lines.append("")

            # Optionally still show some of the matches for manual review
            # if total_matches > 0:
            #     max_show = min(total_matches, 5)
            #     lines.append(f"Showing up to {max_show} matched pairs for manual inspection:")
            #     lines.append("")

            #     for i, pair in enumerate(matched_pairs[:max_show], start=1):
            #         n = pair["normal"]
            #         it = pair["internal"]
            #         value_wei = n.get("value")
            #         time_diff = pair["time_diff_seconds"]

            #         t_n = int(n.get("timeStamp", "0"))
            #         t_i = int(it.get("timeStamp", "0"))
            #         dt_n = datetime.utcfromtimestamp(t_n).isoformat() + "Z"
            #         dt_i = datetime.utcfromtimestamp(t_i).isoformat() + "Z"

            #         lines.append(f"[Match #{i}]")
            #         lines.append(f"- Normal tx: `{n.get('hash')}`")
            #         lines.append(f"- Internal tx: `{it.get('hash')}`")
            #         lines.append(f"- Value (wei): `{value_wei}`")
            #         lines.append(f"- Time diff: `{time_diff}` seconds")
            #         lines.append(f"- Normal time: `{dt_n}`")
            #         lines.append(f"- Internal time: `{dt_i}`")
            #         lines.append("")

            msg = "\n".join(lines)
            if len(msg) > 2000:
                msg = msg[:1900] + "\n...(truncated)..."

            await ctx.send(msg)

        except Exception as e:
            print(f"[TrapCog unexpected error] {type(e).__name__}: {e}")
            await ctx.send(
                "Unexpected error while checking this address. Check bot logs for details."
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(TrapCog(bot))
