# jobs/

- `ingest/`: Python 3.12 (httpx, boto3, pyarrow): ingest-tlc (monthly + replay), ingest-weather, ingest-zones, ingest-gharchive. Each run writes `_manifest.json` and is idempotent by sha256 (S8, Sat Nov 28)
- `transform/`: PySpark raw → Iceberg with DQ rules + quarantine, partition overwrite per day (S9, Sun Nov 29)
