import pickle
from datetime import datetime, timezone, tzinfo

import arxiv

client = arxiv.Client()
batch_size = 1000

search = arxiv.Search(
    query="cat:cs.CV",
    max_results=batch_size,
    sort_by=arxiv.SortCriterion.SubmittedDate,
)

this_week_papers = []
start_of_week = datetime(2024, 11, 3, tzinfo=timezone.utc)

offset = 0
while True:
    results = client.results(search, offset=offset)

    for r in client.results(search):
        if r.updated > start_of_week:
            this_week_papers.append(r)

    if r.updated >= start_of_week:
        offset += batch_size
    else:
        break

print(f"Found {len(this_week_papers)} papers submitted this week.")
with open("this_week_papers.pkl", "wb") as f:
    pickle.dump(this_week_papers, f)
