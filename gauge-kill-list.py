from sugar import Sugar

if __name__ == "__main__":
    ##################### BASE #####################
    chain = "base"
    sugar = Sugar(chain)
    # tokens = sugar.lp_tokens(listed=False)
    lps = sugar.lp_all()

    # unlisted_tokens = tokens[tokens["listed"] == False].index.to_list()
    unlisted_tokens = [
        "0xEFb97aaF77993922aC4be4Da8Fbc9A2425322677",
        "0xe2c86869216aC578bd62a4b8313770d9EE359A05",
        "0x994ac01750047B9d35431a7Ae4Ed312ee955E030",
        "0xEcE7B98bD817ee5B1F2f536dAf34D0B6af8Bb542",
        "0x489fe42C267fe0366B16b0c39e7AEEf977E841eF",
        "0x7ED613AB8b2b4c6A781DDC97eA98a666c6437511",
        "0x00e1724885473B63bCE08a9f0a52F35b0979e35A",
        "0xc43F3Ae305a92043bd9b62eBd2FE14F7547ee485",
        "0xBa5E6fa2f33f3955f0cef50c63dCC84861eAb663",
        "0x04D1963C76EB1BEc59d0eEb249Ed86F736B82993",
        "0x348Fdfe2c35934A96C1353185F09D0F9efBAdA86",
    ]
    lps_gauge_alive = lps[lps["gauge_alive"]]

    lps_gauge_kill = lps_gauge_alive.loc[
        (lps_gauge_alive["token0"].isin(unlisted_tokens))
        | (lps_gauge_alive["token1"].isin(unlisted_tokens)),
        :,
    ]

    COLUMNS_GAUGE_KILL_EXPORT = ["symbol", "gauge"]
    sugar._export_csv(
        lps_gauge_kill.loc[:, COLUMNS_GAUGE_KILL_EXPORT], f"gauge_kill_list_{chain}.csv"
    )

    ##################### OP #####################
    chain = "op"
    sugar = Sugar(chain)
    # tokens = sugar.lp_tokens(listed=False)
    lps = sugar.lp_all()

    # unlisted_tokens = tokens[tokens["listed"] == False].index.to_list()
    unlisted_tokens = [
        "0x47536F17F4fF30e64A96a7555826b8f9e66ec468",
        "0x39FdE572a18448F8139b7788099F0a0740f51205",
        # "0x00e1724885473B63bCE08a9f0a52F35b0979e35A",
        "0xB153FB3d196A8eB25522705560ac152eeEc57901",
        "0x8901cB2e82CC95c01e42206F8d1F417FE53e7Af0",
        "0x7aE97042a4A0eB4D1eB370C34BfEC71042a056B7",
        "0x46f21fDa29F1339e0aB543763FF683D399e393eC",
        "0xb396b31599333739A97951b74652c117BE86eE1D",
        "0x28b42698Caf46B4B012CF38b6C75867E0762186D",
        "0x2513486f18eeE1498D7b6281f668B955181Dd0D9",
        "0xfDeFFc7Ad816BF7867C642dF7eBC2CC5554ec265",
    ]
    lps_gauge_alive = lps[lps["gauge_alive"]]

    lps_gauge_kill = lps_gauge_alive.loc[
        (lps_gauge_alive["token0"].isin(unlisted_tokens))
        | (lps_gauge_alive["token1"].isin(unlisted_tokens)),
        :,
    ]

    COLUMNS_GAUGE_KILL_EXPORT = ["symbol", "gauge"]
    sugar._export_csv(
        lps_gauge_kill.loc[:, COLUMNS_GAUGE_KILL_EXPORT],
        f"gauge_kill_list_{chain}.csv",
    )
