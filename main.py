import csv
from pathlib import Path
from loguru import logger
import pickle
from datetime import datetime, timezone, tzinfo

import arxiv
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
            if r.updated >= start_of_week and "cs.CV" in r.categories:
                batch_papers.append(r)
    except arxiv.UnexpectedEmptyPageError as e:
        logger.warning(e)
        logger.warning("Retrying...")
        continue

    this_week_papers.extend(batch_papers)

    if last_r is not None and last_r.updated >= start_of_week:
        offset += batch_size
    else:
        break

print(f"Found {len(this_week_papers)} papers submitted this week.")

with open("this_week_papers_9_11_2024.csv", "w") as csvfile:
    fieldnames = ["index", "id", "title", "link"]
    writer = csv.DictWriter(
        csvfile,
        fieldnames=fieldnames,
        dialect=csv.unix_dialect,
    )
    writer.writeheader()
    writer.writerows(
        [
            {
                "index": idx,
                "id": paper.get_short_id(),
                "title": paper.title,
                "link": paper.pdf_url,
            }
            for idx, paper in enumerate(this_week_papers)
        ]
    )
