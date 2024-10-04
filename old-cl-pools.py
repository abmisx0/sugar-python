from sugar import Sugar
from dune_client.client import DuneClient
from dune_client.query import QueryBase
import config

if __name__ == "__main__":
    # old cl pools from meow query
    # dune = DuneClient(os.environ["DUNE_API_KEY"])
    dune = DuneClient.from_env()

    # run and fetch query results
    query = QueryBase(query_id=3952558)
    query_result = dune.run_query_dataframe(query=query, ping_frequency=10)
    # fetch query results
    # query_result = dune.get_latest_result_dataframe(3952558)

    old_cl_pools = query_result["pool"].to_list()
    old_cl_names = query_result["name"].to_list()

    ###################### OP ######################
    old_lp_sugar = "0xDa888C610a00686A3cce21b7F4A45A5e52eFa572"
    sugar = Sugar("op", lp_address=old_lp_sugar)
    sugar.relay_all(config.COLUMNS_RELAY_EXPORT, config.COLUMNS_RELAY_EXPORT_RENAME)
    data, block_num = sugar.ve_all(
        columns_export=config.COLUMNS_VENFT_EXPORT,
        columns_rename=config.COLUMNS_VENFT_EXPORT_RENAME,
    )
    sugar.voters(old_cl_pools, block_num, pool_names=old_cl_names, master_export=True)
