import sys
import os
import dotenv
from web3 import Web3
from dune_client.client import DuneClient
from dune_client.query import QueryBase
from geckoterminal_api import GeckoTerminalAPI
import pandas as pd
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sugar import Sugar
import config

WEEK = 7 * 24 * 60 * 60  # 7 days in seconds


def get_old_cl_pools(get_latest=True):
    dune = DuneClient.from_env()
    if get_latest:
        # run and fetch query results
        query = QueryBase(query_id=3952558)
        query_result = dune.run_query_dataframe(query=query, ping_frequency=10)
    else:
        # fetch query results
        query_result = dune.get_latest_result_dataframe(3952558)
    return query_result["pool"].to_list(), query_result["name"].to_list()


def get_voters(pools, names):
    sugar = Sugar("op")
    sugar.relay_all(config.COLUMNS_RELAY_EXPORT, config.COLUMNS_RELAY_EXPORT_RENAME)
    data, block_num = sugar.ve_all(
        columns_export=config.COLUMNS_VENFT_EXPORT,
        columns_rename=config.COLUMNS_VENFT_EXPORT_RENAME,
    )
    sugar.voters(pools, block_num, pool_names=names, master_export=True)


def main():
    # old cl pools from meow query
    old_cl_pools, old_cl_names = get_old_cl_pools(get_latest=True)
    # get voters from old cl pools
    get_voters(old_cl_pools, old_cl_names)


def get_current_epoch_start_ts():
    current_timestamp = int(time.time())  # Get current Unix timestamp
    curr_epoch_start_ts = (current_timestamp // WEEK) * WEEK
    return curr_epoch_start_ts


def get_epoch_start_ts(ts):
    return (ts // WEEK) * WEEK


class OldClPool:
    def __init__(self, chain, lp_address, abi):
        dotenv.load_dotenv()
        try:
            self.chain = chain.lower()
            chain = chain.upper()
            alchemy_key = os.environ[f"RPC_LINK_{chain}"]
            self.w3 = Web3(Web3.HTTPProvider(alchemy_key))
            self.pool = self.w3.eth.contract(address=lp_address, abi=abi)
        except Exception as e:
            raise ValueError(f"Error initializing CLPool: {str(e)}")

    def gauge_fees(self, sugar):
        fees = self.pool.functions.gaugeFees().call()
        token_0 = self.pool.functions.token0().call()
        token_1 = self.pool.functions.token1().call()
        _list = [[token_0, token_1], fees]
        _list = self._process_gauge_fees(_list, sugar)
        return _list

    def _process_gauge_fees(self, _list, sugar):
        tokens = sugar.lp_tokens(listed=False, override=False)
        decimals = (tokens.loc[_list[0][0], "decimals"], tokens.loc[_list[0][1], "decimals"])
        symbols = [tokens.loc[_list[0][0], "symbol"], tokens.loc[_list[0][1], "symbol"]]
        for i in range(2):
            _list[1][i] = sugar.from_wei(_list[1][i], decimals[i]).__float__()
        _list.extend([symbols])
        return _list


if __name__ == "__main__":
    old_cl_lp_sugar_epochs = "0x4C6c4F0d23723d3210cA655Ae156CfCDb7239E7c"  # for epoch calls
    old_cl_lp_sugar_all = "0xb1246E20E865263b0b53355f302e70424B532d2E"  # for all calls
    # old cl pools need their rewards distributed, you can access them by calling CLPool.gaugeFees() method
    old_cl_pool = "0x3241738149B24C9164dA14Fa2040159FFC6Dd237"  # CL100-weth/usdc
    sugar_epochs = Sugar("op", lp_address=old_cl_lp_sugar_epochs)
    sugar_all = Sugar("op", lp_address=old_cl_lp_sugar_all)
    data_epochs = sugar_epochs.lp_epochsByAddress(old_cl_pool)
    data_all = sugar_all.lp_all()
    current_votes = float(data_epochs.loc[0, "votes"])

    usdc_weth_pool = OldClPool("op", old_cl_pool, config.ABI_OLD_CL_POOL_OP)
    gauge_fees_list = usdc_weth_pool.gauge_fees(sugar_epochs)

    gt = GeckoTerminalAPI()
    prices = gt.network_addresses_token_price("optimism", gauge_fees_list[0])
    prices = prices["data"]["attributes"]["token_prices"].values()
    list_prices = list(prices)
    gauge_fees_list.extend([list_prices])
    gauge_fees_list.append(current_votes)

    tokens, fees, symbols, prices, votes = gauge_fees_list
    data = pd.DataFrame(
        {"tokens": [tokens], "fees": [fees], "symbols": [symbols], "prices": [prices], "votes": [votes]}
    )
    data[f"fees_usd_{symbols[0]}"] = data.loc[0, "fees"][0] * float(data.loc[0, "prices"][0])
    data[f"fees_usd_{symbols[1]}"] = data.loc[0, "fees"][1] * float(data.loc[0, "prices"][1])
    data["fees_usd_total"] = data[f"fees_usd_{symbols[0]}"] + data[f"fees_usd_{symbols[1]}"]
    data.to_csv(f"fees_from_{old_cl_pool}.csv", index=False)
