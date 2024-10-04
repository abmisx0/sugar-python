import os
import dotenv
from web3 import Web3
import pandas as pd
import config


class Sugar:
    def __init__(
        self, chain: str, lp_address=None, relay_address=None, ve_address=None
    ):
        """!
        @brief Class to make Sugar calls easily

        @param chain (str): Chain name, (OP, Base, BOB, Mode)
        @param lp_address (str, optional): Custom LpSugar address. Defaults to None.
        @param relay_address (str, optional): Custom RelaySugar address. Defaults to None.
        @param ve_address (str, optional): Custom VeSugar address. Defaults to None.
        """
        # load alchemy keys
        dotenv.load_dotenv()
        try:
            self.chain = chain.lower()
            chain = chain.upper()
            alchemy_key = os.environ[f"RPC_LINK_{chain}"]
            self.w3 = Web3(Web3.HTTPProvider(alchemy_key))
            if lp_address:
                self.lp = self.w3.eth.contract(
                    lp_address, abi=eval(f"config.ABI_LP_SUGAR_{chain}")
                )
            else:
                self.lp = self.w3.eth.contract(
                    eval(f"config.ADDRESS_LP_SUGAR_{chain}"),
                    abi=eval(f"config.ABI_LP_SUGAR_{chain}"),
                )
            if chain in ["OP", "BASE"]:
                if relay_address:
                    self.relay = self.w3.eth.contract(
                        relay_address, abi=eval(f"config.ABI_RELAY_SUGAR_{chain}")
                    )
                else:
                    self.relay = self.w3.eth.contract(
                        eval(f"config.ADDRESS_RELAY_SUGAR_{chain}"),
                        abi=eval(f"config.ABI_RELAY_SUGAR_{chain}"),
                    )
                if ve_address:
                    self.ve = self.w3.eth.contract(
                        ve_address, abi=eval(f"config.ABI_VE_SUGAR_{chain}")
                    )
                else:
                    self.ve = self.w3.eth.contract(
                        eval(f"config.ADDRESS_VE_SUGAR_{chain}"),
                        abi=eval(f"config.ABI_VE_SUGAR_{chain}"),
                    )
            self.connectors = eval(f"config.CONNECTORS_{chain}")
        except Exception:
            print(
                "ERROR: Incorrect chain string. Only these strings accepted: op, base, mode, bob"
            )

    def relay_all(
        self,
        columns_export=None,
        columns_rename=None,
        filter_inactive=True,
        override=True,
    ):
        """!
        @brief Make RelaySugar.all() calls and then store locally with the option to load local data.

        @param columns_export (list, optional): Columns to export. Defaults to None.
        @param columns_rename (dict, optional): Columns to rename. Defaults to None.
        @param filter_inactive (bool, optional): Filter inactive relays. Defaults to True.
        @param override (bool, optional): Fetch onchain state. Defaults to True.

        @return (tuple): Formatted struct as pandas dataframe and block number of first call.
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
            except Exception:
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
        except Exception:
            pass

        data = pd.DataFrame(eval(data_raw), columns=config.COLUMNS_RELAY)
        data.set_index("venft_id", inplace=True)
        for col in config.COLUMNS_RELAY_ETH:
            if col == "votes":
                data[col] = data.apply(
                    lambda row: self._process_votes(
                        row[col], row["used_voting_amount"]
                    ),
                    axis=1,
                )
            else:
                data[col] = data[col].apply(
                    lambda x: self.w3.from_wei(x, "ether").__round__(3)
                )

        # export data
        if filter_inactive:
            data = data[~data["inactive"]]
        if columns_export:
            data = data[columns_export]
        if columns_rename:
            data.rename(columns=columns_rename, inplace=True)
        data.sort_index(inplace=True)

        if override:
            print(data.info())
            path_csv = f"{directory}/relay_all_{self.chain}.csv"
            self._export_csv(data, path_csv, directory)
            return data, block
        else:
            return data, None

    def _process_votes(self, votes, used_voting_amount):
        if not votes:
            return str([])
        return str(
            [
                (
                    tup[0],
                    (self.w3.from_wei(tup[1], "ether") / used_voting_amount)
                    .__round__(3)
                    .__float__(),
                )
                for tup in votes
            ]
        )

    def lp_all(self, limit=500, index_lp=False, override=True):
        """!
        @brief Make LpSugar.all() calls and then store locally with the option to load local data.

        @param limit (int, optional): Number of LPs to fetch during each call. Defaults to 500.
        @param index_lp (bool, optional): Replace index with LP address. Defaults to False.
        @param override (bool, optional): Fetch onchain state. Defaults to True.

        @return (dataframe): Formatted struct as pandas dataframe.
        """
        directory = "data-lp"
        path_data_raw = f"{directory}/raw_lp_all_{self.chain}.txt"

        if override:
            offset = 0
            all_calls = []
            print("\nStating LpSugar.all() calls")
            while True:
                try:
                    call = self.lp.functions.all(
                        limit,
                        offset,
                    ).call()
                    if not call:
                        break
                    all_calls.extend(str(call))
                    offset += limit
                    print(f"{offset = }")
                except Exception:
                    break
            all_calls = str("".join(all_calls)).replace("][", ", ")
            # raw data store
            try:
                f = open(path_data_raw, "w")
            except Exception:
                os.mkdir(f"{directory}")
                f = open(path_data_raw, "w")
            f.write(all_calls)
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
        tokens = self.lp_tokens(listed=False, override=False)
        data_cl = data[data["symbol"] == ""]
        data_cl["symbol"] = data_cl.apply(
            lambda row: f"CL{row['type']}-{tokens.loc[row['token0'], 'symbol']}/{tokens.loc[row['token1'], 'symbol']}",
            axis=1,
        )
        data.update(data_cl)

        if index_lp:
            data.set_index("lp", inplace=True)
        if override:
            print(data.info())
            path_csv = f"{directory}/lp_all_{self.chain}.csv"
            self._export_csv(data, path_csv, directory)
        return data

    def lp_tokens(self, limit=1000, listed=True, override=True):
        """!
        @brief Make LpSugar.tokens() calls and then store locally with the option to load local data.

        @param limit (int, optional): Number of tokens to fetch during each call. Defaults to 1000.
        @param listed (bool, optional): Filter whitelisted tokens. Defaults to True.
        @param override (bool, optional): Fetch onchain state. Defaults to True.

        @return (dataframe): Formatted struct as pandas dataframe.
        """
        directory = "data-lp"
        path_data_raw = f"{directory}/raw_lp_tokens_{self.chain}.txt"

        if override:
            offset = 0
            all_calls = []
            print("\nStating LpSugar.tokens() calls")
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
                    all_calls.extend(str(call))
                    offset += limit
                    print(f"{offset = }")
                except Exception:
                    break
            all_calls = str("".join(all_calls)).replace("][", ", ")
            # raw data store
            try:
                f = open(path_data_raw, "w")
            except Exception:
                os.mkdir(f"{directory}")
                f = open(path_data_raw, "w")
            f.write(all_calls)
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
            data = data[data["listed"]]
        if override:
            print(data.info())
            path_csv = f"{directory}/lp_tokens_{self.chain}.csv"
            self._export_csv(data, path_csv, directory)
        return data

    def ve_all(
        self,
        limit=800,
        columns_export=None,
        columns_rename=None,
        weights=True,
        override=True,
    ):
        """!
        @brief Make VeSugar.all() calls and then store locally with the option to load local data.

        @param limit (int, optional): Number of veNFTs to fetch during each call. Defaults to 800.
        @param columns_export (list, optional): Columns to export. Defaults to None.
        @param columns_rename (dict, optional): Columns to rename. Defaults to None.
        @param weights (bool, optional): Change voting amount to weights. Defaults to True.
        @param override (bool, optional): Fetch onchain state. Defaults to True.

        @return (tuple): Formatted struct as pandas dataframe and block number of first call.
        """
        relay, _ = self.relay_all(filter_inactive=False, override=False)
        relay_idx = set(relay.index)
        relay_idx = sorted(relay_idx)
        relay_len = len(relay_idx)

        directory = "data-ve"
        path_data_raw = f"{directory}/raw_ve_all_{self.chain}.txt"

        if override:
            all_calls = []
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
                    if not call:
                        break
                    if count == 0:
                        _limit = limit
                    all_calls.extend(str(call))
                    _offset = call[-1][0] + 1
                    print(f"{_offset = }")
                    if call:
                        del call
                except Exception:
                    _limit = max(_limit // 2, 1)
                    if _limit == 1:
                        _offset += 1
                        _limit = limit
                    count += 1
            all_calls = str("".join(all_calls)).replace("][", ", ")
            try:
                f = open(path_data_raw, "w")
            except Exception:
                os.mkdir(f"{directory}")
                f = open(path_data_raw, "w")
            f.write(all_calls)
            f.close()

        # read raw data
        f = open(path_data_raw, "r")
        data_raw = f.read()
        f.close()

        try:
            print(f"\n{block = }\n")
        except Exception:
            pass

        data = pd.DataFrame(eval(data_raw), columns=config.COLUMNS_VENFT)
        data.drop_duplicates(inplace=True, subset="id")
        data.set_index("id", inplace=True)
        for col in config.COLUMNS_VENFT_ETH:
            if col == "votes":
                data[col] = data.apply(
                    lambda row: self._process_ve_votes(
                        row[col], row["governance_amount"], weights
                    ),
                    axis=1,
                )
            else:
                data[col] = data[col].apply(
                    lambda x: self.w3.from_wei(x, "ether").__round__(3)
                )

        if columns_export:
            data = data[columns_export]
        if columns_rename:
            data.rename(columns=columns_rename, inplace=True)
        if override:
            print(data.info())
            path_csv = f"{directory}/ve_all_{self.chain}.csv"
            self._export_csv(data, path_csv, directory)
            return data, block
        else:
            return data, None

    def _process_ve_votes(self, votes, governance_amount, weights):
        if not votes:
            return str([])
        if weights:
            return str(
                [
                    (
                        tup[0],
                        min((self.w3.from_wei(tup[1], "ether") / governance_amount), 1)
                        .__round__(3)
                        .__float__(),
                    )
                    for tup in votes
                    if governance_amount != 0
                ]
            )
        else:
            return str(
                [
                    (tup[0], self.w3.from_wei(tup[1], "ether").__round__(3).__float__())
                    for tup in votes
                ]
            )

    def voters(self, pool_address, block_num, pool_names=None, master_export=True):
        """!
        @brief Filter for voters on any amount of pools. Defaults to exporting locally.

        @param pool_address (str | list): Pool address or list of pool addresses
        @param block_num (int): Block number from ve_all() call.
        @param pool_names (list, optional): Pool names ordered in the same way as pool_address. Defaults to None.
        @param master_export (bool, optional): Aggregate voter data into one dataframe. Defaults to True.
        """
        if isinstance(pool_address, str):
            pool_address = [pool_address]
        cols = ["account", "governance_amount", "votes"]
        data_ve, _ = self.ve_all(columns_export=cols, weights=False, override=False)
        data_lp = self.lp_all(index_lp=True, override=False)

        flg_master = True
        for addy in pool_address:
            matches = []
            votes = []
            for venft, row in data_ve.iterrows():
                if row["governance_amount"] == 0:
                    continue
                ray = eval(row["votes"])
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
            except Exception:
                symbol = pool_names[pool_address.index(addy)] if pool_names else None
                symbol_file = symbol.replace("/", "-") if symbol else None

            directory = "data-voters"
            if symbol_file:
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

    def relay_depositors(self, mveNFT_ID, block_num):
        """!
        @brief Filter for depositors in a particular relay. Defaults to exporting locally.

        @param mveNFT_ID (int): Managed veNFT ID of the relay.
        @param block_num (int): Block number from ve_all() call.
        """
        cols = ["account", "governance_amount", "managed_id"]
        data, _ = self.ve_all(columns_export=cols, weights=False, override=False)
        data = data[data["managed_id"] == mveNFT_ID]

        data["locks"] = data.index
        total_votes = data.groupby("account")["governance_amount"].sum()
        venfts = (
            data.groupby("account")["locks"]
            .apply(list)
            .apply(lambda x: str(x).strip("[]"))
        )
        data = pd.concat([total_votes, venfts], axis=1).sort_values(
            "governance_amount", ascending=False
        )

        relay, _ = self.relay_all(filter_inactive=False, override=False)
        relay_name = relay.loc[mveNFT_ID, "name"].replace(" ", "_")

        print(data.info())

        directory = "data-relay-depositors"
        path_csv = (
            f"{directory}/relay_depositors_{self.chain}_{block_num}_{relay_name}.csv"
        )
        self._export_csv(data, path_csv, directory)

    def _export_csv(self, df, path, directory=None):
        try:
            df.to_csv(path)
        except Exception:
            os.mkdir(f"{directory}")
            df.to_csv(path)


if __name__ == "__main__":
    ##################### BASE #####################
    sugar = Sugar("base")
    # sugar.relay_all(config.COLUMNS_RELAY_EXPORT, config.COLUMNS_RELAY_EXPORT_RENAME)
    # sugar.lp_tokens(listed=False)
    # sugar.lp_all()

    # data, block_num = sugar.ve_all(
    #     columns_export=config.COLUMNS_VENFT_EXPORT,
    #     columns_rename=config.COLUMNS_VENFT_EXPORT_RENAME,
    # )
    block_num = 20612812

    pools = [
        "0x70aCDF2Ad0bf2402C957154f944c19Ef4e1cbAE1",
        "0x4e962BB3889Bf030368F56810A9c96B83CB3E778",
    ]
    # sugar.voters(pools, block_num, master_export=False)

    sugar.relay_depositors(12435, block_num)

    ###################### OP ######################
    # sugar = Sugar("op")
    # sugar.relay_all(config.COLUMNS_RELAY_EXPORT, config.COLUMNS_RELAY_EXPORT_RENAME)
    # sugar.lp_tokens()
    # sugar.lp_all()

    # data, block_num = sugar.ve_all(
    #     columns_export=config.COLUMNS_VENFT_EXPORT,
    #     columns_rename=config.COLUMNS_VENFT_EXPORT_RENAME,
    # )

    # sugar.relay_depositors(20697, block_num)

    ##################### MODE #####################
    # sugar = Sugar("mode")
    # sugar.lp_tokens()
