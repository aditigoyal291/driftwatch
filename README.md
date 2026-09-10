# DriftWatch

**AI-powered schema drift detection for lakehouse tables** — catches breaking changes in your data pipelines before they break downstream dashboards and models.

> Status: 🚧 Work in progress — see [Roadmap](#roadmap) below.

---

## The Problem

Modern data platforms ingest from dozens of external sources — CRMs, support tools, marketing platforms, internal databases. Every one of those sources is owned by a *different team*, often outside the data org's control.

When someone on an upstream source's admin team renames a field, or an API starts returning a new data type, nothing tells the data team directly. What actually happens, in most companies, looks like this:

1. An ingestion job silently loads bad or null data — or hard-fails.
2. Downstream tables and dbt models quietly compute wrong numbers, or break outright.
3. Someone notices a dashboard looks off — hours or days later.
4. An engineer manually digs through logs, diffs the old and new schema by hand, and traces which of the dozens of downstream tables are affected.

That reactive loop — silent failure, delayed discovery, manual diagnosis — is the real cost of schema drift. It's rarely just "a column changed." It's "nobody knew for hours, and figuring out the blast radius took an engineer's whole afternoon."

## What DriftWatch Does

DriftWatch continuously watches a lakehouse's table schemas, automatically detects changes that could break downstream pipelines, and uses an LLM to explain **what changed, why it likely happened, what's affected, and how to fix it** — turning a multi-hour manual investigation into a report an engineer reads in two minutes.

It's a scoped-down version of the same category of tooling used by modern data observability platforms, built to demonstrate the core mechanics end to end.

## How It Works

```
 ┌─────────────┐     ┌──────────────┐     ┌───────────────┐     ┌──────────────┐     ┌────────────┐
 │  Lakehouse  │ ──▶ |   Snapshot   │ ──▶ │    Detect      │ ──▶ │   Diagnose    │ ──▶ │   Notify   │
 │  (Iceberg)  │     │  table schema │     │  schema drift  │     │  (AI-powered) │     │ Slack/CLI  │
 └─────────────┘     └──────────────┘     └───────────────┘     └──────────────┘     └────────────┘
```

1. **Snapshot** — On a schedule, DriftWatch reads each table's current schema and lightweight stats (row counts, null rates, distinct values on key columns) and stores it as a point-in-time snapshot.
2. **Detect** — It compares the new snapshot against the last one and runs a set of rules against the diff: did a column's type change? Was a column dropped? Did a null rate spike unexpectedly? Each finding is tagged with a severity.
3. **Diagnose** — For meaningful drift events, the diff and surrounding context are sent to an LLM, which returns a structured incident report: likely root cause, which downstream tables/models are affected, and a suggested fix.
4. **Notify** — The report is delivered to Slack or the console, so an engineer opens their laptop to a clear explanation and a next step — not a raw stack trace.

## Why It Matters

Schema drift is one of the most common causes of silent data pipeline failures, and most teams only find out once a dashboard is visibly wrong. DriftWatch closes that gap by catching drift the moment it happens and doing the first-pass investigation automatically, instead of leaving that work entirely to an on-call engineer.

## Demo Data

DriftWatch ships with a self-contained local lakehouse (Iceberg tables backed by local Parquet files, seeded with synthetic data modeled on common ingestion sources like CRM and support-ticket tables) plus a script that intentionally introduces schema changes over time. This means the entire project — lake, drift, detection, and diagnosis — can be run and demoed with a single command, with no external infrastructure or credentials required.

## Tech Stack

| Layer | Tools |
|---|---|
| Language | Python 3.11+ |
| Lakehouse | Apache Iceberg (via PyIceberg), Parquet |
| Data validation | Pydantic |
| Concurrency | asyncio |
| AI diagnosis | LLM API with structured/validated output |
| CLI | Typer |
| Testing | pytest |
| Packaging | pyproject.toml, GitHub Actions CI |
| Containerization | Docker, Docker Compose |
| Deployment reference | Kubernetes CronJob manifest (see `k8s/`) |

## Roadmap

- [ ] Core schema snapshot + drift detection engine
- [ ] AI diagnosis layer with structured incident reports
- [ ] CLI (`driftwatch watch`, `driftwatch diagnose`)
- [ ] Local Iceberg demo environment with synthetic data + drift simulation
- [ ] Dockerized one-command demo
- [ ] CI pipeline (tests, linting, type checking)
- [ ] Kubernetes CronJob manifest for production-style scheduling

## License

MIT
