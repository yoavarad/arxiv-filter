import csv
from pathlib import Path
from loguru import logger
import pickle
from datetime import datetime, timezone, tzinfo

import arxiv
import pandas as pd
from tqdm import tqdm

client = arxiv.Client()
batch_size = 1000

search = arxiv.Search(
    query="cat:cs.CV",
    max_results=batch_size,
    sort_by=arxiv.SortCriterion.LastUpdatedDate,
)

this_week_papers: list[arxiv.Result] = []
start_of_week = datetime(2024, 11, 3, tzinfo=timezone.utc)

offset = 0
while True:
    logger.info(f"Searching with {offset=:,}, found={len(this_week_papers):,}")
    results = client.results(search, offset=offset)

    batch_papers = []
    try:
        for r in tqdm(
            client.results(search),
            total=batch_size,
            desc="Processing batch",
        ):
            last_r = r
            if r.published >= start_of_week and "cs.CV" in r.categories:
                batch_papers.append(r)
    except arxiv.UnexpectedEmptyPageError as e:
        logger.warning(e)
        logger.warning("Retrying...")
        continue

    this_week_papers.extend(batch_papers)

    if last_r is not None and last_r.published >= start_of_week:
        offset += batch_size
    else:
        break


processed = {}
for paper in this_week_papers:
    processed[paper.get_short_id().split("v")[0]] = {
        "id": paper.get_short_id(),
        "title": paper.title,
        "link": paper.pdf_url,
        "published": paper.published.astimezone(timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
    }
processed_df = pd.DataFrame(processed.values())
print(f"Found {len(processed_df)} papers submitted this week.")
processed_df.to_csv("this_week_papers_9_11_2024.csv", index=True)
