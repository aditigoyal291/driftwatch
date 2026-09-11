"""Local PyIceberg SqlCatalog factory for DriftWatch demos and connectors."""

from pathlib import Path

from pyiceberg.catalog.sql import SqlCatalog


def get_local_catalog(
    catalog_db_path: str | Path, warehouse_dir: str | Path
) -> SqlCatalog:
    """Return a SqlCatalog configured for local SQLite metadata + file warehouse.

    Wraps PyIceberg's local SqlCatalog setup so callers do not need to know the
    specific URI/warehouse configuration details.
    """
    db_path = Path(catalog_db_path).resolve()
    warehouse_path = Path(warehouse_dir).resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    warehouse_path.mkdir(parents=True, exist_ok=True)

    return SqlCatalog(
        "driftwatch_local",
        uri=f"sqlite:///{db_path.as_posix()}",
        # Plain filesystem path (not file:// URI): PyIceberg/PyArrow on Windows
        # mishandles file:///C:/... warehouse URIs.
        warehouse=str(warehouse_path),
    )
