# Export Reference

The library writes two kinds of files: **explicit exports** you request via
`export_dataframe(...)`, and **automatic snapshots** captured on every fetch.

## Explicit exports

`client.export_dataframe(df, name, subdirectory="data", include_block=True)`
writes a CSV under `<export_dir>/<subdirectory>/`. `export_dir` is set on the
client (defaults to the current directory):

```python
client = SugarClient(ChainId.BASE, export_dir="output")
client.export_dataframe(pools, "pools")                       # output/data/pools_{chain}_{block}.csv
client.export_dataframe(tokens, "tokens", include_block=False)  # output/data/tokens_{chain}.csv
```

Filenames are `{name}_{chain}.csv` or `{name}_{chain}_{block}.csv` when
`include_block=True`. `{chain}` is `chain_name.lower()`.

The bundled examples write here:

| Script | Output |
| --- | --- |
| `export_pools.py` | `output/data/tokens_{chain}.csv`, `output/data/pools_{chain}_{block}.csv` |
| `quickstart.py` | prints to terminal |
| `ve_holders.py` | prints to terminal |
| `list_relays.py` | prints to terminal |

## Automatic snapshots

Every fetch is also indexed to the snapshot store (Sugar contracts only serve
real-time state, so snapshots build a local history). Layout:

```
sugar-snapshots/<chain>/<dataset>/<block>.parquet|csv.gz
sugar-snapshots/<chain>/<dataset>/manifest.jsonl
```

- Root defaults to `./sugar-snapshots`, overridable via `SUGAR_SNAPSHOT_DIR` or
  `SugarClient(..., snapshot_dir=...)`.
- Disable with `SugarClient(..., snapshot=False)`.
- Read back with `client.load_snapshot(dataset, block=...)` and
  `client.snapshot_history(dataset)`.

## Chain name reference

`{chain}` is `chain_name.lower()`: `base`, `optimism`, `mode`, `lisk`,
`fraxtal`, `ink`, `soneium`, `metal`, `celo`, `superseed`, `swell`, `unichain`.
