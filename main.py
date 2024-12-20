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

from httpx import AsyncClient, Response

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
    "cryptodungeon": Project(
        "stars1cctq6q3caw050sk6wfhruq2dlyslunuuhl0hq6yy32g4qkn5yn4qm6r5wg", 1, 400
    ),
    "mad_scientist_stars": Project(
        "stars1v8avajk64z7pppeu45ce6vv8wuxmwacdff484lqvv0vnka0cwgdqdk64sf", 1, 10_000
    ),
    # "mad_scientist_osmo": Project(  # only manually run for now
    #     "osmo16pwjh09s662a0j2ssmzauyvkvagjwd9kpwc0mtamlwr8dtznlhfqcweap6", 1, 10_000
    # ),
}


def get_rest_api_endpoint(network: str = "stars") -> str:
    # https://cosmos.directory/stargaze/nodes

    if network.startswith("osmo"):
        return random.choice(
            [
                "https://api.osmosis.validatus.com",
                "https://osmosis-api.polkachu.com",
                "https://osmosis.rest.stakin-nodes.com",
                "https://rest.osmosis.goldenratiostaking.net",
                "https://community.nuxian-node.ch:6797/osmosis/crpc",
                "https://osmosis-lcd.quickapi.com",
                "https://osmosis-api.stake-town.com",
                "https://rest-osmosis.ecostake.com",
                "https://osmosis-api.w3coins.io",
                "https://lcd.osmosis.zone",
                "https://api-osmosis.cosmos-spaces.cloud",
                "https://osmosis-api.lavenderfive.com",
                "https://osmosis-mainnet-lcd.autostake.com",
                "https://osmosis-rest.publicnode.com",
                "https://rest.cros-nest.com/osmosis",
                "https://osmosis-rest.interstellar-lounge.org",
                "https://api-osmosis-01.stakeflow.io",
            ]
        )

    return random.choice(
        [
            "https://api.stargaze.silentvalidator.com",
            "https://stargaze-api.ibs.team",
            # "https://stargaze-api.chainroot.io", # 429s
            "https://stargaze-api.ramuchi.tech",
            "https://stargaze-api.kleomedes.network",
            "https://stargaze-api.ibs.team",
            "https://api-stargaze.d-stake.xyz",
            # "https://stargaze-api.polkachu.com",
        ]
    )


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
    print(f"Fetching {token_id} from {url}")

    success = True
    response: Response = None
    try:
        # fetching raw state would be so much nicer yea?
        response = await client.get(url)
        if response.status_code != 200:
            success = False
    except Exception as e:
        print(f"Error fetching {token_id}: Exception: {e} (url: {url} )")
        success = False

    if success:
        results[token_id] = response.json()
    else:
        try_again[token_id] = try_again.get(token_id, 0) + 1

        if response != None:
            if try_again[token_id] < 3:
                print(
                    f"[!] Retry: {token_id}: {response.status_code} status. Trying again in 5 seconds (May be burned, or in a DAO)."
                )
                await asyncio.sleep(15)
                await fetch_data(client, url, token_id, results)
            else:
                print(
                    f"Final: Error fetching {token_id}: {response.status_code} status. This NFT may not exist. Either END_IDX {PROJECT.end_idx} is too high, or the NFT was burned."
                )


async def async_holders():
    results = {}

    urls = {}
    for i in range(PROJECT.start_idx, PROJECT.end_idx + 1):
        # TODO: Don't get the URL here, instead we can generate that randomly in fetch data. Then handle there w/ round robin.
        urls[i] = get_url(
            get_rest_api_endpoint(PROJECT.contract_addr), PROJECT.contract_addr, i
        )

    async with AsyncClient(timeout=60.0) as client:
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
