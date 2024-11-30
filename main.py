import json
from pathlib import Path
from typing import Optional
from loguru import logger
from datetime import datetime, timezone

import arxiv
import pandas as pd
from tqdm import tqdm

start_of_week = datetime(2024, 11, 24, tzinfo=timezone.utc)
output_file = "this_week_papers_30_11_2024.csv"


client = arxiv.Client()
batch_size = 1000

search = arxiv.Search(
    query="cat:cs.CV",
    max_results=batch_size,
    sort_by=arxiv.SortCriterion.LastUpdatedDate,
)

this_week_papers: list[arxiv.Result] = []


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


def get_abs_link_or_none(paper: arxiv.Result) -> Optional[str]:
    for link in paper.links:
        if link.href.startswith("http://arxiv.org/abs/"):
            return link.href


processed = {}
for paper in this_week_papers:
    processed[paper.get_short_id().split("v")[0]] = {
        "id": paper.get_short_id(),
        "title": paper.title,
        "pdf_link": paper.pdf_url,
        "abs_link": get_abs_link_or_none(paper),
        "published": paper.published,
    }

df = pd.DataFrame(processed.values())
df = df.loc[df["published"] >= start_of_week]
relevant_df = (
    df.loc[~df["title"].apply(is_boring)]
    .sort_values("published", ascending=True)  # From old to new
    .reset_index(drop=True)
)
logger.info(
    f"Found {len(relevant_df):,}/{len(df):,} ({len(relevant_df)/len(df):.2%}) *relevant* papers submitted this week."
)
relevant_df.to_csv(
    output_file, index=True, columns=["title", "abs_link", "pdf_link", "published"]
)
logger.info(f"Saved to {output_file}")
