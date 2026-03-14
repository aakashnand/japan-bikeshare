# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A scheduled data pipeline that fetches GBFS (General Bikeshare Feed Specification) feeds from Japan's ODPT public API and archives snapshots to a private HuggingFace dataset.

## Setup

```bash
pip install -r requirements.txt
```

Required environment variables:
- `HF_TOKEN` — HuggingFace write access token
- `HF_USERNAME` — HuggingFace username (dataset repo owner)

## Running the Pipeline

```bash
# Fetch and upload daily static feeds (station_information, system_information)
python -m src.fetch --frequency daily

# Fetch and upload realtime feeds (station_status)
python -m src.fetch --frequency realtime
```

## Architecture

**Data flow:** GitHub Actions → `src/fetch.py` → ODPT API → gzip-compressed JSON → `src/upload.py` → HuggingFace dataset

**Key components:**
- `config/feeds.json` — defines providers (docomo, openstreet/hellocycling) and which feed types to fetch per frequency
- `src/fetch.py` — fetches from `https://api-public.odpt.org/api/v4/gbfs/{slug}/{feed}.json`, injects `poll_timestamp` (UTC), compresses with gzip. Realtime paths use `YYYYMMDD_HHMM`, daily paths use `YYYY-MM-DD`
- `src/upload.py` — creates the HuggingFace private dataset repo if absent, uploads compressed blobs

**Scheduling:**
- `poll_static.yml` — GitHub Actions cron at `0 15 * * *` (00:00 JST) for daily feeds
- `poll_status.yml` — `workflow_dispatch` only (triggered externally by cron-job.org) for realtime feeds