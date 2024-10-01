import os
import dotenv
from web3 import Web3
import pandas as pd
import numpy as np
import config


class Sugar:
    """Class to make Sugar calls"""

    def __init__(self, chain: str):
        # load alchemy keys
        dotenv.load_dotenv()
        try:
            self.chain = chain.lower()
            chain = chain.upper()
            alchemy_key = os.environ[f"RPC_LINK_{chain}"]
            self.w3 = Web3(Web3.HTTPProvider(alchemy_key))
            self.lp = self.w3.eth.contract(eval(f"config.ADDRESS_LP_SUGAR_{chain}"), abi=eval(f"config.ABI_LP_SUGAR_{chain}"))  # type: ignore
            if chain in ["OP", "BASE"]:
                self.relay = self.w3.eth.contract(eval(f"config.ADDRESS_RELAY_SUGAR_{chain}"), abi=eval(f"config.ABI_RELAY_SUGAR_{chain}"))  # type: ignore
                self.ve = self.w3.eth.contract(eval(f"config.ADDRESS_VE_SUGAR_{chain}"), abi=eval(f"config.ABI_VE_SUGAR_{chain}"))  # type: ignore
            self.connectors = eval(f"config.CONNECTORS_{chain}")
        except:
            return print(
                "ERROR: Incorrect chain string. Only these strings accepted: op, base, mode, bob"
            )

    def relay_all(
        self,
        columns_export=[],
        columns_rename={},
        filter_inactive=True,
        export=True,
        override=True,
    ):
        """Calls relaySugar.all() and exports as csv

        Args:
            override (bool, optional): True will force a rpc call. Defaults to False.
        """
        directory = "data-relay"
        path_data_raw = f"{directory}/raw_relay_all_{self.chain}.txt"

        if override:
            block = self.w3.eth.block_number
            print("\nStating RelaySugar.all() call\n")
            call = self.relay.functions.all(
                "0x0000000000000000000000000000000000000000"
            ).call()
            # raw data store
            try:
                f = open(path_data_raw, "w")
            except:
                os.mkdir(f"{directory}")
                f = open(path_data_raw, "w")
            f.write(str(call))
            f.close()

        # read relay data
        f = open(path_data_raw, "r")
        data_raw = f.read()
        f.close()

        try:
            print(f"\n{block = }\n")
        except:
            pass

        # trim data into a copy/paste format for the rest of the BD team on google sheets
        data = pd.DataFrame(eval(data_raw), columns=config.COLUMNS_RELAY)
        data.set_index("venft_id", inplace=True)
        for col in config.COLUMNS_RELAY_ETH:
            if col == "votes":
                for row in data.index:
                    ray = data.loc[row, col]
                    if not ray:
                        continue
                    new_ray = []
                    for tup in ray:
                        i = (
                            self.w3.from_wei(tup[1], "ether")
                            / data.loc[row, "used_voting_amount"]
                        )
                        new_ray.append((tup[0], i.__round__(3).__float__()))
                    data.loc[row, col] = str(new_ray)
            else:
                for row in data.index:
                    i = data.loc[row, col]
                    data.loc[row, col] = self.w3.from_wei(i, "ether").__round__(3)

        # export data
        if filter_inactive:
            filt = data["inactive"] == False
            if columns_export:
                data = data.loc[filt, columns_export]
            else:
                data = data.loc[filt]
        else:
            if columns_export:
                data = data.loc[:, columns_export]
        if columns_rename:
            data.rename(columns=columns_rename, inplace=True)
        data.sort_index(inplace=True)

        if export:
            print(data.info())
            path_csv = f"{directory}/relay_all_{self.chain}.csv"
            self._export_csv(data, path_csv, directory)
        else:
            return data

    def lp_all(self, limit=500, index_lp=False, export=True, override=True):
        directory = "data-lp"
        path_data_raw = f"{directory}/raw_lp_all_{self.chain}.txt"

        if override:
            offset = 0
            calls = []
            print("\nStating LpSugar.all() calls")
            while True:
                try:
                    call = self.lp.functions.all(
                        limit,
                        offset,
                    ).call()
                    offset += limit
                    calls = np.append(calls, str(call))
                    print(f"{offset = }")
                    if call == []:
                        break
                except:
                    break
            calls = str("".join(calls)).replace("][", ", ")
            # raw data store
            try:
                f = open(path_data_raw, "w")
            except:
                os.mkdir(f"{directory}")
                f = open(path_data_raw, "w")
            f.write(calls)
            f.close()

        # read raw data
        f = open(path_data_raw, "r")
        data_raw = f.read()
        f.close()

        if self.chain == "op":
            data = pd.DataFrame(eval(data_raw), columns=config.COLUMNS_LP)
        else:
            data = pd.DataFrame(eval(data_raw), columns=config.COLUMNS_LP[0:-1])
        data.drop_duplicates(inplace=True)

        # load lp_tokens data to give CL pairs a name like on the FE
        # note: turn this into a method later ??
        tokens = self.lp_tokens(listed=False, export=False, override=False)
        data_cl = data[data["symbol"] == ""]
        for row in data_cl.index:
            tick = data_cl.loc[row, "type"]
            symbol0 = tokens.loc[data_cl.loc[row, "token0"], "symbol"]
            symbol1 = tokens.loc[data_cl.loc[row, "token1"], "symbol"]
            data_cl.loc[row, "symbol"] = f"CL{tick}-{symbol0}/{symbol1}"
        data[data["symbol"] == ""] = data_cl

        if index_lp:
            data.set_index("lp", inplace=True)

        if export:
            print(data.info())
            path_csv = f"{directory}/lp_all_{self.chain}.csv"
            self._export_csv(data, path_csv, directory)
        else:
            return data

    def lp_tokens(self, limit=1000, listed=True, export=True, override=True):
        directory = "data-lp"
        path_data_raw = f"{directory}/raw_lp_tokens_{self.chain}.txt"

        if override:
            offset = 0
            calls = []
            print("\nStating LpSugar.all() calls")
            while True:
                try:
                    call = self.lp.functions.tokens(
                        limit,
                        offset,
                        "0x0000000000000000000000000000000000000000",
                        self.connectors,
                    ).call()
                    if len(call) == len(self.connectors):
                        break
                    offset += limit
                    print(f"{offset = }")
                    calls = np.append(calls, str(call))
                except:
                    break
            calls = str("".join(calls)).replace("][", ", ")
            # raw data store
            try:
                f = open(path_data_raw, "w")
            except:
                os.mkdir(f"{directory}")
                f = open(path_data_raw, "w")
            f.write(calls)
            f.close()

        # read raw data
        f = open(path_data_raw, "r")
        data_raw = f.read()
        f.close()

        data = pd.DataFrame(eval(data_raw), columns=config.COLUMNS_TOKEN)
        data.drop_duplicates(inplace=True)
        data.set_index("token_address", inplace=True)
        data.drop("account_balance", axis=1, inplace=True)
        if listed:
            data = data[data["listed"] == True]

        if export:
            print(data.info())
            path_csv = f"{directory}/lp_tokens_{self.chain}.csv"
            self._export_csv(data, path_csv, directory)
        else:
            return data

    def ve_all(
        self,
        limit=800,
        columns_export=[],
        columns_rename={},
        weights=True,
        export=True,
        override=True,
    ):
        relay = self.relay_all(filter_inactive=False, export=False, override=False)
        relay_idx = relay.index.to_list()
        relay_idx = sorted(relay_idx)
        relay_len = len(relay_idx)

        directory = "data-ve"
        path_data_raw = f"{directory}/raw_ve_all_{self.chain}.txt"

        if override:
            calls = []
            _offset = 1
            _limit = limit
            block = self.w3.eth.block_number
            i = 0
            count = 0
            print("\nStating veSugar.all() calls")
            while True:
                # efficient pass of relay veNFTs
                if i < relay_len:
                    relay_num = relay_idx[i]
                    if _offset <= relay_num < (_offset + _limit):
                        if relay_num == _offset:
                            _offset += 1
                        elif relay_num > _offset:
                            _limit = relay_num - _offset
                        if relay_num < _offset:
                            i += 1
                            count = 0
                    elif relay_num < _offset:
                        i += 1
                        count = 0
                try:
                    call = self.ve.functions.all(_limit, _offset).call()
                    if call == []:
                        break
                    _offset = call[-1][0] + 1
                    if count == 0:
                        _limit = limit
                    calls = np.append(calls, str(call))
                    print(f"{_offset = }")
                    if call:
                        del call
                except:
                    _limit = _limit // 2
                    if _limit <= 1:
                        _offset += 1
                        _limit = limit
                    count += 1
            calls = str("".join(calls)).replace("][", ", ")
            try:
                f = open(path_data_raw, "w")
            except:
                os.mkdir(f"{directory}")
                f = open(path_data_raw, "w")
            f.write(calls)
            f.close()

        # read raw data
        f = open(path_data_raw, "r")
        data_raw = f.read()
        f.close()

        try:
            print(f"\n{block = }\n")
        except:
            pass

        data = pd.DataFrame(eval(data_raw), columns=config.COLUMNS_VENFT)
        data.drop_duplicates(inplace=True, subset="id")
        data.set_index("id", inplace=True)
        for col in config.COLUMNS_VENFT_ETH:
            if col == "votes":
                for row in data.index:
                    ray = data.loc[row, col]
                    if not ray:
                        continue
                    new_ray = []
                    for tup in ray:
                        if weights:
                            if data.loc[row, "governance_amount"] == 0:
                                i = 0
                                continue
                            i = (
                                self.w3.from_wei(tup[1], "ether")
                                / data.loc[row, "governance_amount"]
                            )
                            if i > 1:
                                i = 1
                        else:
                            i = self.w3.from_wei(tup[1], "ether")
                        new_ray.append((tup[0], i.__round__(3).__float__()))
                    data.loc[row, col] = str(new_ray)
            else:
                for row in data.index:
                    i = data.loc[row, col]
                    data.loc[row, col] = self.w3.from_wei(i, "ether").__round__(3)
        if columns_export:
            data = data.loc[:, columns_export]
        if columns_rename:
            data.rename(columns=columns_rename, inplace=True)

        if export:
            print(data.info())
            path_csv = f"{directory}/ve_all_{self.chain}.csv"
            self._export_csv(data, path_csv, directory)
        else:
            return data

    def voters(self, pool_address, block_num, pool_names=[], master_export=True):
        if pool_address.__class__ == str:
            pool_address = [pool_address]
        cols = ["account", "governance_amount", "votes"]
        data_ve = self.ve_all(
            columns_export=cols, export=False, weights=False, override=False
        )
        data_lp = self.lp_all(index_lp=True, export=False, override=False)

        flg_master = True
        for addy in pool_address:
            matches = []
            votes = []
            for venft in data_ve.index:
                if data_ve.loc[venft, "governance_amount"] == 0:
                    continue
                ray = data_ve.loc[venft, "votes"]
                if not ray:
                    continue
                ray = eval(ray)
                for tup in ray:
                    if tup[0].lower() == addy.lower():
                        matches.append(venft)
                        votes.append(tup[1])

            # use matches to filter old dataset with matching addy to create a new dataset
            data = data_ve.loc[matches, :].copy()
            data["governance_amount"] = votes
            data["locks"] = matches  # new data series

            total_votes = data.groupby("account")["governance_amount"].sum()
            venfts = (
                data.groupby("account")["locks"]
                .apply(list)
                .apply(lambda x: str(x).strip("[]"))
            )

            data = pd.concat([total_votes, venfts], axis=1).sort_values(
                "governance_amount", ascending=False
            )

            try:
                symbol = data_lp.loc[addy, "symbol"]
                symbol_file = symbol.replace("/", "-")
            except:
                symbol_file = None
                if pool_names:
                    symbol = pool_names[pool_address.index(addy)]
                    symbol_file = symbol.replace("/", "-")

            directory = "data-voters"
            if symbol_file is not None:
                path_csv = (
                    f"{directory}/voters_{self.chain}_{block_num}_{symbol_file}.csv"
                )
            else:
                path_csv = f"{directory}/voters_{self.chain}_{block_num}_{addy}.csv"

            if master_export:
                data_mod = data.copy()
                data_mod["name"] = symbol  # new data series
                if flg_master:
                    data_master = data_mod.copy()
                    flg_master = False
                else:
                    data_master = pd.concat([data_master, data_mod])
            else:
                self._export_csv(data, path_csv, directory)

        if master_export:
            total_votes = data_master.groupby("account")["governance_amount"].sum()
            venfts = (
                data_master.groupby("account")["locks"]
                .apply(list)
                .apply(lambda x: str(x).strip("[]").replace("'", ""))
            )
            names = (
                data_master.groupby("account")["name"]
                .apply(list)
                .apply(lambda x: str(x).strip("['']").replace("'", ""))
            )
            data = pd.concat([total_votes, names, venfts], axis=1).sort_values(
                "governance_amount", ascending=False
            )
            path_csv = f"{directory}/voters_{self.chain}_{block_num}_master.csv"
            self._export_csv(data, path_csv, directory)

    def relay_depositors(self, mveNFT_ID, block_num, columns_export=[]):
        data = self.ve_all(
            columns_export=columns_export, export=False, weights=False, override=False
        )
        data = data[data["managed_id"] == mveNFT_ID].sort_values(
            "governance_amount", ascending=False
        )

        if columns_export:
            data = data.loc[:, columns_export]
        print(data.info())

        directory = "data-relay-depositors"
        path_csv = (
            f"{directory}/relay_depositors_{self.chain}_{block_num}_{mveNFT_ID}.csv"
        )
        self._export_csv(data, path_csv, directory)

    def _export_csv(self, df, path, directory=None):
        try:
            df.to_csv(path)
        except:
            os.mkdir(f"{directory}")
            df.to_csv(path)


if __name__ == "__main__":
    # columns_voters_export = [
    #     "account",
    #     "governance_amount",
    #     "votes",
    # ]
    columns_relay_depositors_export = [
        "account",
        "governance_amount",
        "managed_id",
    ]

    ##################### BASE #####################
    sugar_base = Sugar("base")
    sugar_base.relay_all(
        config.COLUMNS_RELAY_EXPORT, config.COLUMNS_RELAY_EXPORT_RENAME
    )
    sugar_base.lp_tokens()
    sugar_base.lp_all()

    sugar_base.ve_all(
        columns_export=config.COLUMNS_VENFT_EXPORT,
        columns_rename=config.COLUMNS_VENFT_EXPORT_RENAME,
    )
    # block_num = 20470613

    # pools = [
    #     "0x70aCDF2Ad0bf2402C957154f944c19Ef4e1cbAE1",
    #     "0x4e962BB3889Bf030368F56810A9c96B83CB3E778",
    # ]
    # sugar_base.voters(pools, block_num, master_export=False)

    # sugar_base.relay_depositors(12435, block_num, columns_relay_depositors_export)

    ###################### OP ######################
    # sugar_op = Sugar("op")
    # sugar_op.relay_all(config.COLUMNS_RELAY_EXPORT, config.COLUMNS_RELAY_EXPORT_RENAME)
    # sugar_op.lp_tokens()
    # sugar_op.lp_all()

    # sugar_op.ve_all(
    #     columns_export=config.COLUMNS_VENFT_EXPORT,
    #     columns_rename=config.COLUMNS_VENFT_EXPORT_RENAME,
    # )
    # block_num = 126056896

    # sugar_op.relay_depositors(20697, block_num, columns_relay_depositors_export)

    # data = sugar_op.ve_all(
    #     columns_export=config.COLUMNS_VENFT_EXPORT,
    #     columns_rename=config.COLUMNS_VENFT_EXPORT_RENAME,
    #     export=False,
    #     override=False,
    # )
    # data["locks"] = data.index
    # total_votes = data.groupby("account")["governance_amount"].sum()
    # venfts = (
    #     data.groupby("account")["locks"].apply(list).apply(lambda x: str(x).strip("[]"))
    # )
    # data = pd.concat([total_votes, venfts], axis=1).sort_values(
    #     "governance_amount", ascending=False
    # )
    # sugar_op._export_csv(data, f"veVELO_holders_{block_num}")

    ##################### MODE #####################
    # sugar_mode = Sugar("mode")
    # sugar_mode.lp_tokens()
