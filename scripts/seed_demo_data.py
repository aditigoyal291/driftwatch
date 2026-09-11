"""Generate synthetic CRM-style Parquet tables for local DriftWatch demos."""

from datetime import datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from faker import Faker

DATA_DIR = Path("data")
ROW_COUNT = 200
DEAL_STAGES = (
    "prospecting",
    "qualification",
    "proposal",
    "negotiation",
    "closed_won",
    "closed_lost",
)


def build_deals_table(fake: Faker, rows: int = ROW_COUNT) -> pa.Table:
    """Build a synthetic deals table."""
    return pa.table(
        {
            "deal_id": list(range(1, rows + 1)),
            "account_name": [fake.company() for _ in range(rows)],
            "deal_amount": [
                round(fake.pyfloat(min_value=500, max_value=250_000, right_digits=2), 2)
                for _ in range(rows)
            ],
            "stage": [fake.random_element(elements=DEAL_STAGES) for _ in range(rows)],
            "created_at": [
                fake.date_time_between(start_date="-2y", end_date="now")
                for _ in range(rows)
            ],
        }
    )


def build_contacts_table(fake: Faker, rows: int = ROW_COUNT) -> pa.Table:
    """Build a synthetic contacts table."""
    return pa.table(
        {
            "contact_id": list(range(1, rows + 1)),
            "full_name": [fake.name() for _ in range(rows)],
            "email": [fake.company_email() for _ in range(rows)],
            "company": [fake.company() for _ in range(rows)],
        }
    )


def main() -> None:
    """Write deals and contacts Parquet files under ./data/ (overwrite if present)."""
    fake = Faker()
    Faker.seed(42)
    fake.seed_instance(42)

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    tables: dict[str, pa.Table] = {
        "deals": build_deals_table(fake),
        "contacts": build_contacts_table(fake),
    }

    written: list[Path] = []
    for name, table in tables.items():
        path = DATA_DIR / f"{name}.parquet"
        pq.write_table(table, path)
        written.append(path)

    print(f"Wrote {len(written)} Parquet file(s) to {DATA_DIR.resolve()}:")
    for path in written:
        print(f"  - {path.name} ({path.stat().st_size} bytes)")
    print(f"Generated at {datetime.now().isoformat(timespec='seconds')}")


if __name__ == "__main__":
    main()
