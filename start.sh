#!/bin/bash
set -e

echo "Starting Torrent IMDB Parser..."


# Download IMDb datasets if not already present.
mkdir -p data/imdb
if [ ! -f data/imdb/title.basics.tsv.gz ]; then
    echo "Downloading IMDb title.basics dataset..."
    curl -fL --retry 3 -o data/imdb/title.basics.tsv.gz \
        https://datasets.imdbws.com/title.basics.tsv.gz
fi
if [ ! -f data/imdb/title.episode.tsv.gz ]; then
    echo "Downloading IMDb title.episode dataset..."
    curl -fL --retry 3 -o data/imdb/title.episode.tsv.gz \
        https://datasets.imdbws.com/title.episode.tsv.gz
fi

echo "Launching API on port 7860..."
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 7860
