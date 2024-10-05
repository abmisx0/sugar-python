import os
import dotenv
from web3 import Web3
import pandas as pd
import config
from functools import lru_cache, wraps
from typing import Optional, List, Tuple, Union, Callable, TypeVar, ParamSpec

P = ParamSpec("P")
R = TypeVar("R")


def documented_cache(maxsize: int = None) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    A wrapper for lru_cache that preserves the original function's docstring.

    Args:
        maxsize: The maximum size of the cache (passed to lru_cache)

    Returns:
        A decorator that applies lru_cache while preserving the docstring
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        @lru_cache(maxsize=maxsize)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            return func(*args, **kwargs)

        return wrapper

    return decorator


class Sugar:
    def __init__(
        self,
        chain: str,
        lp_address: Optional[str] = None,
        relay_address: Optional[str] = None,
        ve_address: Optional[str] = None,
    ):
        """
        Initialize the Sugar class for making Sugar calls easily.

        Args:
            chain (str): Chain name (OP, Base, BOB, Mode).
            lp_address (str, optional): Custom LpSugar address. Defaults to None.
            relay_address (str, optional): Custom RelaySugar address. Defaults to None.
            ve_address (str, optional): Custom VeSugar address. Defaults to None.
        """
        dotenv.load_dotenv()
        try:
            self.chain = chain.lower()
            chain = chain.upper()
            alchemy_key = os.environ[f"RPC_LINK_{chain}"]
            self.w3 = Web3(Web3.HTTPProvider(alchemy_key))
            self.lp = self._initialize_contract("LP", lp_address, chain)
            if chain in ["OP", "BASE"]:
                self.relay = self._initialize_contract("RELAY", relay_address, chain)
                self.ve = self._initialize_contract("VE", ve_address, chain)
            self.connectors = getattr(config, f"CONNECTORS_{chain}")
        except Exception as e:
            raise ValueError(f"Error initializing Sugar: {str(e)}")

    def _initialize_contract(self, contract_type: str, address: Optional[str], chain: str):
        """
        Initialize a contract object.

        Args:
            contract_type (str): Type of contract.
            address (Optional[str]): Address of the contract.
            chain (str): Chain name.

        Returns:
            Contract: Contract object.
        """
        if address:
            return self.w3.eth.contract(address, abi=getattr(config, f"ABI_{contract_type}_SUGAR_{chain}"))
        else:
            return self.w3.eth.contract(
                getattr(config, f"ADDRESS_{contract_type}_SUGAR_{chain}"),
                abi=getattr(config, f"ABI_{contract_type}_SUGAR_{chain}"),
            )

    @documented_cache(maxsize=32)
    def relay_all(
        self,
        columns_export: Optional[Tuple[str]] = None,
        columns_rename: Optional[frozenset] = None,
        filter_inactive: bool = True,
        override: bool = True,
    ) -> Tuple[pd.DataFrame, Optional[int]]:
        """
        Make RelaySugar.all() calls and store locally with the option to load local data.

        Args:
            columns_export (Tuple[str], optional): Columns to export. Defaults to None.
            columns_rename (frozenset, optional): Columns to rename. Defaults to None.
            filter_inactive (bool, optional): Filter inactive relays. Defaults to True.
            override (bool, optional): Fetch onchain state. Defaults to True.

        Returns:
            Tuple[pd.DataFrame, Optional[int]]: Formatted struct as pandas dataframe and block number of first call.
        """
        directory = "data-relay"
        path_data_raw = f"{directory}/raw_relay_all_{self.chain}.txt"

        if override:
            block = self.w3.eth.block_number
            print("\nStating RelaySugar.all() call\n")
            call = self.relay.functions.all("0x0000000000000000000000000000000000000000").call()
            os.makedirs(directory, exist_ok=True)
            call = str(call)
            with open(path_data_raw, "w") as f:
                f.write(call)
        else:
            with open(path_data_raw, "r") as f:
                call = f.read()
            block = None

        if block:
            print(f"{block = }")

        data = pd.DataFrame(eval(call), columns=config.COLUMNS_RELAY)
        data.set_index("venft_id", inplace=True)
        for col in config.COLUMNS_RELAY_ETH:
            if col == "votes":
                data[col] = data.apply(
                    lambda row: self._process_votes(row[col], row["used_voting_amount"]),
                    axis=1,
                )
            else:
                data[col] = data[col].apply(lambda x: self.w3.from_wei(x, "ether").__round__(3))

        if filter_inactive:
            data = data[~data["inactive"]]
        if columns_export:
            data = data[list(columns_export)]
        if columns_rename:
            data.rename(columns=dict(columns_rename), inplace=True)
        data.sort_index(inplace=True)

        if override:
            path_csv = f"{directory}/relay_all_{self.chain}.csv"
            self._export_csv(data, path_csv, directory)

        return data, block

    def _process_votes(self, votes, used_voting_amount):
        """
        Process votes from RelaySugar.

        Args:
            votes (str): Votes as a string.
            used_voting_amount (int): Used voting amount.

        Returns:
            str: Processed votes.
        """
        if not votes:
            return str([])
        return str(
            [
                (
                    tup[0],
                    (self.w3.from_wei(tup[1], "ether") / used_voting_amount).__round__(3).__float__(),
                )
                for tup in votes
            ]
        )

    @documented_cache(maxsize=32)
    def lp_tokens(self, limit: int = 1000, listed: bool = True, override: bool = True) -> pd.DataFrame:
        """
        Make LpSugar.tokens() calls and store locally with the option to load local data.

        Args:
            limit (int, optional): Number of tokens to fetch during each call. Defaults to 1000.
            listed (bool, optional): Filter whitelisted tokens. Defaults to True.
            override (bool, optional): Fetch onchain state. Defaults to True.

        Returns:
            pd.DataFrame: Formatted struct as pandas dataframe.
        """
        directory = "data-lp"
        path_data_raw = f"{directory}/raw_lp_tokens_{self.chain}.txt"

        if override:
            all_calls = self._fetch_lp_tokens(limit)
            os.makedirs(directory, exist_ok=True)
            with open(path_data_raw, "w") as f:
                f.write(all_calls)
        else:
            with open(path_data_raw, "r") as f:
                all_calls = f.read()

        data = self._process_lp_tokens(all_calls, listed)

        if override:
            path_csv = f"{directory}/lp_tokens_{self.chain}.csv"
            self._export_csv(data, path_csv, directory)

        return data

    def _fetch_lp_tokens(self, limit: int) -> str:
        """
        Fetch lp tokens from LpSugar.

        Args:
            limit (int): Number of tokens to fetch during each call. Defaults to 1000.

        Returns:
            str: All calls as a string.
        """
        offset = 0
        all_calls = []
        print("\nStarting LpSugar.tokens() calls\n")
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
        return str("".join(all_calls)).replace("][", ", ")

    def _process_lp_tokens(self, all_calls: str, listed: bool) -> pd.DataFrame:
        """
        Process lp tokens from LpSugar.

        Args:
            all_calls (str): All calls as a string.
            listed (bool): Filter whitelisted tokens.

        Returns:
            pd.DataFrame: Formatted struct as pandas dataframe.
        """
        data = pd.DataFrame(eval(all_calls), columns=config.COLUMNS_TOKEN)
        data.drop_duplicates(inplace=True)
        data.set_index("token_address", inplace=True)
        data.drop("account_balance", axis=1, inplace=True)
        if listed:
            data = data[data["listed"]]
        return data

    @documented_cache(maxsize=32)
    def lp_all(self, limit: int = 500, index_lp: bool = False, override: bool = True) -> pd.DataFrame:
        """
        Make LpSugar.all() calls and store locally with the option to load local data.

        Args:
            limit (int, optional): Number of LPs to fetch during each call. Defaults to 500.
            index_lp (bool, optional): Replace index with LP address. Defaults to False.
            override (bool, optional): Fetch onchain state. Defaults to True.

        Returns:
            pd.DataFrame: Formatted struct as pandas dataframe.
        """
        directory = "data-lp"
        path_data_raw = f"{directory}/raw_lp_all_{self.chain}.txt"

        if override:
            all_calls = self._fetch_lp_all(limit)
            os.makedirs(directory, exist_ok=True)
            with open(path_data_raw, "w") as f:
                f.write(all_calls)
        else:
            with open(path_data_raw, "r") as f:
                all_calls = f.read()

        data = self._process_lp_all(all_calls, index_lp)

        if override:
            path_csv = f"{directory}/lp_all_{self.chain}.csv"
            self._export_csv(data, path_csv, directory)

        return data

    def _fetch_lp_all(self, limit: int) -> str:
        """
        Fetch lp all from LpSugar.

        Args:
            limit (int): Number of LPs to fetch during each call. Defaults to 500.

        Returns:
            str: All calls as a string.
        """
        offset = 0
        all_calls = []
        print("\nStarting LpSugar.all() calls\n")
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
        return str("".join(all_calls)).replace("][", ", ")

    def _process_lp_all(self, all_calls: str, index_lp: bool) -> pd.DataFrame:
        """
        Process lp all from LpSugar.

        Args:
            all_calls (str): All calls as a string.
            index_lp (bool): Replace index with LP address.

        Returns:
            pd.DataFrame: Formatted struct as pandas dataframe.
        """
        if self.chain == "op":
            data = pd.DataFrame(eval(all_calls), columns=config.COLUMNS_LP)
        else:
            data = pd.DataFrame(eval(all_calls), columns=config.COLUMNS_LP[0:-1])
        data.drop_duplicates(inplace=True)

        tokens = self.lp_tokens(listed=False, override=False)
        data_cl = data[data["symbol"] == ""]
        data_cl["symbol"] = data_cl.apply(
            lambda row: f"CL{row['type']}-{tokens.loc[row['token0'], 'symbol']}/{tokens.loc[row['token1'], 'symbol']}",
            axis=1,
        )
        data.update(data_cl)

        if index_lp:
            data.set_index("lp", inplace=True)
        return data

    @documented_cache(maxsize=32)
    def ve_all(
        self,
        limit: int = 800,
        columns_export: Optional[Tuple[str]] = None,
        columns_rename: Optional[frozenset] = None,
        weights: bool = True,
        index_id: bool = True,
        override: bool = True,
    ) -> Tuple[pd.DataFrame, Optional[int]]:
        """
        Make VeSugar.all() calls and store locally with the option to load local data.

        Args:
            limit (int, optional): Number of veNFTs to fetch during each call. Defaults to 800.
            columns_export (Tuple[str], optional): Columns to export. Defaults to None.
            columns_rename (frozenset, optional): Columns to rename. Defaults to None.
            weights (bool, optional): Change voting amount to weights. Defaults to True.
            index_id (bool, optional): Use ID as index. Defaults to True.
            override (bool, optional): Fetch onchain state. Defaults to True.

        Returns:
            Tuple[pd.DataFrame, Optional[int]]: Formatted struct as pandas dataframe and block number of first call.
        """
        relay, _ = self.relay_all(filter_inactive=False, override=False)
        relay_idx = sorted(set(relay.index))
        relay_len = len(relay_idx)

        directory = "data-ve"
        path_data_raw = f"{directory}/raw_ve_all_{self.chain}.txt"

        if override:
            all_calls, block = self._fetch_ve_all(limit, relay_idx, relay_len)
            os.makedirs(directory, exist_ok=True)
            with open(path_data_raw, "w") as f:
                f.write(all_calls)
        else:
            with open(path_data_raw, "r") as f:
                all_calls = f.read()
            block = None

        if block:
            print(f"\n{block = }")

        data = self._process_ve_all(all_calls, columns_export, columns_rename, weights, index_id)

        if override:
            path_csv = f"{directory}/ve_all_{self.chain}.csv"
            self._export_csv(data, path_csv, directory)

        return data, block

    def _fetch_ve_all(self, limit: int, relay_idx: List[int], relay_len: int) -> Tuple[str, int]:
        """
        Fetch ve all from VeSugar.

        Args:
            limit (int): Number of veNFTs to fetch during each call. Defaults to 800.
            relay_idx (List[int]): Relay indices.
            relay_len (int): Length of relay indices.

        Returns:
            Tuple[str, int]: All calls as a string and block number of first call.
        """
        all_calls = []
        _offset = 1
        _limit = limit
        block = self.w3.eth.block_number
        i = 0
        count = 0
        print("\nStarting veSugar.all() calls\n")
        while True:
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
            except Exception:
                _limit = max(_limit // 2, 1)
                if _limit == 1:
                    _offset += 1
                    _limit = limit
                count += 1
        return str("".join(all_calls)).replace("][", ", "), block

    def _process_ve_all(
        self,
        all_calls: str,
        columns_export: Optional[Tuple[str]],
        columns_rename: Optional[frozenset],
        weights: bool,
        index_id: bool,
    ) -> pd.DataFrame:
        """
        Process ve all from VeSugar.

        Args:
            all_calls (str): All calls as a string.
            columns_export (Tuple[str], optional): Columns to export. Defaults to None.
            columns_rename (frozenset, optional): Columns to rename. Defaults to None.
            weights (bool): Change voting amount to weights.
            index_id (bool): Use ID as index.

        Returns:
            pd.DataFrame: Formatted struct as pandas dataframe.
        """
        data = pd.DataFrame(eval(all_calls), columns=config.COLUMNS_VENFT)
        data.drop_duplicates(inplace=True, subset="id")
        if index_id:
            data.set_index("id", inplace=True)
        elif index_id is False and "id" not in list(columns_export):
            columns_export = tuple(["id"] + list(columns_export))

        for col in config.COLUMNS_VENFT_ETH:
            if col == "votes":
                data[col] = data.apply(
                    lambda row: self._process_ve_votes(row[col], row["governance_amount"], weights),
                    axis=1,
                )
            else:
                data[col] = data[col].apply(lambda x: self.w3.from_wei(x, "ether").__round__(3))

        if columns_export:
            data = data[list(columns_export)]
        if columns_rename:
            data.rename(columns=dict(columns_rename), inplace=True)
        return data

    def _process_ve_votes(self, votes, governance_amount, weights):
        """
        Process ve votes.

        Args:
            votes (str): Votes as a string.
            governance_amount (int): Governance amount.
            weights (bool): Change voting amount to weights.

        Returns:
            str: Processed votes.
        """
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
                [(tup[0], self.w3.from_wei(tup[1], "ether").__round__(3).__float__()) for tup in votes]
            )

    def voters(
        self,
        pool_address: Union[str, Tuple[str]],
        block_num: int,
        pool_names: Optional[Tuple[str]] = None,
        master_export: bool = True,
    ):
        """
        Filter for voters on any amount of pools. Defaults to exporting locally.

        Args:
            pool_address (Union[str, Tuple[str]]): Pool address or tuple of pool addresses.
            block_num (int): Block number from ve_all() call.
            pool_names (Tuple[str], optional): Pool names ordered in the same way as pool_address. Defaults to None.
            master_export (bool, optional): Aggregate voter data into one dataframe. Defaults to True.
        """
        if isinstance(pool_address, str):
            pool_address = (pool_address,)
        cols = ("account", "governance_amount", "votes")
        data_ve, _ = self.ve_all(columns_export=cols, weights=False, override=False)
        data_lp = self.lp_all(index_lp=True, override=False)

        data_master = pd.DataFrame()
        for addy in pool_address:
            data = self._process_voters(data_ve, addy)
            symbol, symbol_file = self._get_symbol(data_lp, addy, pool_address, pool_names)

            if master_export:
                data_mod = data.copy()
                data_mod["name"] = symbol
                data_master = pd.concat([data_master, data_mod])
            else:
                directory = "data-voters"
                path_csv = f"{directory}/voters_{self.chain}_{block_num}_{symbol_file or addy}.csv"
                self._export_csv(data, path_csv, directory)

        if master_export:
            self._export_master_voters(data_master, block_num)

    def _process_voters(self, data_ve: pd.DataFrame, addy: str) -> pd.DataFrame:
        """
        Process voters.

        Args:
            data_ve (pd.DataFrame): Dataframe with veNFT data.
            addy (str): Address to filter.

        Returns:
            pd.DataFrame: Formatted struct as pandas dataframe.
        """
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

        data = data_ve.loc[matches, :].copy()
        data["governance_amount"] = votes
        data["locks"] = matches

        total_votes = data.groupby("account")["governance_amount"].sum()
        venfts = data.groupby("account")["locks"].apply(list).apply(lambda x: str(x).strip("[]"))

        return pd.concat([total_votes, venfts], axis=1).sort_values("governance_amount", ascending=False)

    def _get_symbol(
        self,
        data_lp: pd.DataFrame,
        addy: str,
        pool_address: Tuple[str],
        pool_names: Optional[Tuple[str]],
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Get symbol from LpSugar.

        Args:
            data_lp (pd.DataFrame): Dataframe with LP data.
            addy (str): Address to filter.
            pool_address (Tuple[str]): Pool addresses.
            pool_names (Optional[Tuple[str]]): Pool names.

        Returns:
            Tuple[Optional[str], Optional[str]]: Symbol and symbol file.
        """
        try:
            symbol = data_lp.loc[addy, "symbol"]
            symbol_file = symbol.replace("/", "-")
        except Exception:
            symbol = pool_names[pool_address.index(addy)] if pool_names else None
            symbol_file = symbol.replace("/", "-") if symbol else None
        return symbol, symbol_file

    def _export_master_voters(self, data_master: pd.DataFrame, block_num: int):
        """
        Export master voters.

        Args:
            data_master (pd.DataFrame): Dataframe with voter data.
            block_num (int): Block number.
        """
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
        directory = "data-voters"
        path_csv = f"{directory}/voters_{self.chain}_{block_num}_master.csv"
        self._export_csv(data, path_csv, directory)

    def relay_depositors(self, mveNFT_ID: int, block_num: int):
        """
        Filter for depositors in a particular relay. Defaults to exporting locally.

        Args:
            mveNFT_ID (int): Managed veNFT ID of the relay.
            block_num (int): Block number from ve_all() call.
        """
        cols = ("id", "account", "governance_amount", "managed_id")
        data, _ = self.ve_all(columns_export=cols, weights=False, index_id=False, override=False)
        data = data[data["managed_id"] == mveNFT_ID]

        grouped = (
            data.groupby("account")
            .agg({"governance_amount": "sum", "id": lambda x: str(list(x)).strip("[]")})
            .rename(columns={"id": "locks"})
        )

        data = grouped.sort_values("governance_amount", ascending=False)

        relay, _ = self.relay_all(filter_inactive=False, override=False)
        relay_name = relay.loc[mveNFT_ID, "name"].replace(" ", "_")

        directory = "data-relay-depositors"
        path_csv = f"{directory}/relay_depositors_{self.chain}_{block_num}_{relay_name}.csv"
        self._export_csv(data, path_csv, directory)

    def _export_csv(self, df: pd.DataFrame, path: str, directory: Optional[str] = None) -> None:
        """
        Export dataframe to csv.

        Args:
            df (pd.DataFrame): Dataframe to export.
            path (str): Path to export to.
            directory (Optional[str], optional): Directory to export to. Defaults to None.
        """
        if directory:
            os.makedirs(directory, exist_ok=True)
        df.to_csv(path, index=True)


if __name__ == "__main__":
    ##################### BASE #####################
    sugar = Sugar("base")
    sugar.relay_all(config.COLUMNS_RELAY_EXPORT, config.COLUMNS_RELAY_EXPORT_RENAME)
    sugar.lp_tokens(listed=False)
    sugar.lp_all()

    data, block_num = sugar.ve_all(
        columns_export=config.COLUMNS_VENFT_EXPORT,
        columns_rename=config.COLUMNS_VENFT_EXPORT_RENAME,
    )
    # block_num = 20657276

    pools = (
        "0x70aCDF2Ad0bf2402C957154f944c19Ef4e1cbAE1",
        "0x4e962BB3889Bf030368F56810A9c96B83CB3E778",
    )
    sugar.voters(pools, block_num, master_export=False)
    sugar.voters(pools, block_num, master_export=True)

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
