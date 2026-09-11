"""Seed a local Iceberg catalog with the same CRM demo tables as Parquet seed."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from faker import Faker

from driftwatch.iceberg_catalog import get_local_catalog
from seed_demo_data import ROW_COUNT, build_contacts_table, build_deals_table

DATA_DIR = Path("data")
CATALOG_DB = DATA_DIR / "iceberg_catalog.db"
WAREHOUSE_DIR = DATA_DIR / "iceberg_warehouse"
NAMESPACE = "demo"
TABLE_BUILDERS = {
    "deals": build_deals_table,
    "contacts": build_contacts_table,
}


def main() -> None:
    """Create demo Iceberg tables and load synthetic rows (safely re-runnable)."""
    fake = Faker()
    Faker.seed(42)
    fake.seed_instance(42)

    catalog = get_local_catalog(CATALOG_DB, WAREHOUSE_DIR)
    catalog.create_namespace_if_not_exists(NAMESPACE)

    print(f"Iceberg catalog DB: {CATALOG_DB.resolve()}")
    print(f"Iceberg warehouse:  {WAREHOUSE_DIR.resolve()}")
    print(f"Namespace: {NAMESPACE}")

    for table_name, builder in TABLE_BUILDERS.items():
        identifier = f"{NAMESPACE}.{table_name}"
        arrow_table = builder(fake, rows=ROW_COUNT)

        # Drop-and-recreate (not append): seed_demo_data.py overwrites Parquet
        # files each run. create_table_if_not_exists + append would duplicate
        # rows on re-run, and would not refresh schema if the seed shape changes.
        # Dropping first keeps this script idempotent with a clean 200-row load.
        if catalog.table_exists(identifier):
            catalog.drop_table(identifier)

        iceberg_table = catalog.create_table(
            identifier,
            schema=arrow_table.schema,
            properties={"format-version": "2"},
        )
        iceberg_table.append(arrow_table)

        print(f"\nWrote {identifier}: {arrow_table.num_rows} rows")
        print(f"Iceberg schema for {identifier}:")
        print(iceberg_table.schema())

    print(f"\nGenerated at {datetime.now().isoformat(timespec='seconds')}")


if __name__ == "__main__":
    main()
