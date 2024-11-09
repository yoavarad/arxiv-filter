import json
from pathlib import Path
from loguru import logger
from datetime import datetime, timezone

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


def load_boring_words() -> list[str]:
    return json.loads(Path("boring_words.json").read_text())


boring_words = load_boring_words()


def is_boring(title: str) -> bool:
    for word in boring_words:
        if word in title:
            return True
    return False


logger.debug(f"Boring words: {boring_words}")

offset = 0
while True:
    logger.info(f"Searching with {offset=:,}, found={len(this_week_papers):,}")
    results = client.results(search, offset=offset)

    try:
        batch_papers: list[arxiv.Result] = list(
            tqdm(
                client.results(search),
                total=batch_size,
                desc="Processing batch",
            )
        )
    except arxiv.UnexpectedEmptyPageError as e:
        logger.warning(e)
        logger.warning("Retrying...")
        continue

    this_week_papers.extend(batch_papers)

    if this_week_papers[-1].published >= start_of_week:
        offset += batch_size
    else:
        break


processed = {}
for paper in this_week_papers:
    processed[paper.get_short_id().split("v")[0]] = {
        "id": paper.get_short_id(),
        "title": paper.title,
        "link": paper.pdf_url,
        "published": paper.published,
    }
df = pd.DataFrame(processed.values())
print(f"Found {len(df)} papers submitted this week.")
this_week_df = df.loc[df["published"] >= start_of_week]
this_week_df = this_week_df.loc[~this_week_df["title"].apply(is_boring)]
df.to_csv("this_week_papers_9_11_2024.csv", index=True)
