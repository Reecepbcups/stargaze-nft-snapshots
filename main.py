"""
Reecepbcups | Apr 8th, 2024

Takes a snapshot of all Stargaze NFT holders really quickly with async query requests.
Then saves these into an easy JSON file you can iterate.

$ python3 main.py badkids
"""

import asyncio
import datetime
import json
import os
import random

from httpx import AsyncClient

from helpers import CompactJSONEncoder, Project, fmt_time, get_contract_info, get_url

curr_dir = os.path.dirname(os.path.realpath(__file__))

REQUIRED_WALLET_PREFIX = "stars"


PROJECTS = {
    "badkids": Project(
        "stars19jq6mj84cnt9p7sagjxqf8hxtczwc8wlpuwe4sh62w45aheseues57n420", 1, 9_999
    ).name_override("badkids"),
    "bitkids": Project(
        "stars1pqcldy82fcmptkzvzakwlv3gtpgupewc3e3q598mg5nrr25rv40qpu0z5v", 1, 9_999
    ),
    "celestine_sloth_society": Project(
        "stars10n0m58ztlr9wvwkgjuek2m2k0dn5pgrhfw9eahg9p8e5qtvn964suc995j", 1, 2_500
    ),
    "racoon": Project(
        "stars1hsl7mqpntmskc88mkw28ywz66m9qtn9z7skmpp8lal6uwjfngerqr45km9", 1, 1_333
    ),
    "cryptoniummaker": Project(
        "stars1g2ptrqnky5pu70r3g584zpk76cwqplyc63e8apwayau6l3jr8c0sp9q45u", 1, 5_500
    ),
    "afterthefilter": Project(
        "stars1nf53vw5mulj9y6f66vxj2j98mkpny5nm46lkwytjk9wuj6ccsp2s34n6na", 1, 9_999
    ),
    "pixelsquids": Project(
        "stars1xca9ex0zgacct0fu0lzqzqrve0ys74aa345d2cxu3zrl7rpke9mqh528at", 1, 4_444
    ),
    "sneaky": Project(
        "stars1429tk3pj6nrta2y34gx0njrm8zum53v05dyjawlsk6w84wqugsnshf2n3x", 1, 999
    ),
    "geckies": Project(
        "stars166kqwcu8789xh7nk07fcrdzek54205u8gzas684lnas2kzalksqsg5xhqf", 1, 5_000
    ),
    "rektbulls": Project(
        "stars1ts5ymnra9wv27eqty8x88lhty4svea2j6jkw20t3mnnne6jwk5fqplsrdg", 1, 2269
    ),
}


def get_rest_api_endpoint() -> str:
    # https://cosmos.directory/stargaze/nodes
    rpcs = [
        "https://stargaze-api.polkachu.com",
        "https://api-stargaze.pupmos.network",
        "https://api.stargaze.silentvalidator.com",
        "https://api-stargaze.d-stake.xyz",
        "https://stargaze-api.ibs.team",
    ]

    return random.choice(rpcs)


PROJECT_NAME = ""
PROJECT = None

if len(os.sys.argv) > 1:
    PROJECT_NAME = os.sys.argv[1]
    if PROJECT_NAME in PROJECTS.keys():
        PROJECT = PROJECTS[PROJECT_NAME]
    else:
        print(f"Invalid project. Must be one of {PROJECTS.keys()}")
        os.sys.exit(1)

if PROJECT is None or PROJECT_NAME == "":
    print(f"Please provide a project to snapshot. Must be one of {PROJECTS.keys()}")
    os.sys.exit(1)

# create NFT directories
for collection in PROJECTS.keys():
    os.makedirs(os.path.join(curr_dir, collection), exist_ok=True)


# == MAIN LOGIC ==

try_again: dict[str, int] = {}


async def fetch_data(client: AsyncClient, url: str, token_id: int, results: dict):
    # async with httpx.AsyncClient() as client:
    print(f"Fetching {token_id} from {url}")

    response = await client.get(url)

    if response.status_code == 200:
        results[token_id] = response.json()

    else:
        try_again[token_id] = try_again.get(token_id, 0) + 1

        if try_again[token_id] < 2:
            print(
                f"[!] Retry: {token_id}: {response.status_code} status. Trying again in 5 seconds (May be burned, or in a DAO)."
            )
            await asyncio.sleep(5)
            await fetch_data(client, url, token_id, results)
        else:
            print(
                f"Error fetching {token_id}: {response.status_code} status. This NFT may not exist. Either END_IDX {PROJECT.end_idx} is too high, or the NFT was burned."
            )


async def async_holders():
    results = {}

    urls = {}
    for i in range(PROJECT.start_idx, PROJECT.end_idx + 1):
        # TODO: Don't get the URL here, instead we can generate that randomly in fetch data. Then handle there w/ round robin.
        urls[i] = get_url(get_rest_api_endpoint(), PROJECT.contract_addr, i)

    async with AsyncClient(timeout=30.0) as client:
        tasks = [fetch_data(client, url, key, results) for key, url in urls.items()]
        await asyncio.gather(*tasks)

    # Save holders to file in an easier to digest format
    holders: dict[str, list[int]] = {}

    for k, v in results.items():
        owner = v.get("data", {}).get("owner", None)
        if owner is None:
            continue

        if owner not in holders:
            holders[owner] = []

        holders[owner].append(k)

    # sort holders by the most NFTs (at the top) to least (bottom) in the file.
    holders = {
        k: sorted(v)
        for k, v in sorted(holders.items(), key=lambda item: len(item[1]), reverse=True)
    }

    # get parent contract info
    info = get_contract_info(get_rest_api_endpoint(), PROJECT.contract_addr)

    now = datetime.datetime.now()
    fileName = f"{fmt_time(now)}.json"
    internalTime = fmt_time(now, "%Y-%m-%d %H:%M:%S")

    name = info.get("contract_info", {}).get("label", None)
    if PROJECT.name != "":
        name = PROJECT.name

    # save holders to a file
    with open(
        os.path.join(curr_dir, PROJECT_NAME, fileName),
        "w",
    ) as f:
        print("Saving results to file")

        json.dump(
            {
                "contract": {
                    "address": PROJECT.contract_addr,
                    "name": name,
                    "code_id": info.get("contract_info", {}).get("code_id", None),
                    "unique_holders": len(holders.keys()),
                },
                "time": internalTime,
                "range": {"start": PROJECT.start_idx, "end": PROJECT.end_idx},
                "holders": holders,
            },
            f,
            cls=CompactJSONEncoder,
        )


if __name__ == "__main__":
    asyncio.run(async_holders())
