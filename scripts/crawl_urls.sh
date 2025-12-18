#!/usr/bin/env bash
set -e
set -x

ITEM_SELECTOR="#block-info-advan > div:nth-child(2) > div"
MIN_DATE="01/12/2020"
MAX_DATE="18/12/2025"
MAX_PAGES=19
OUTPUT_FILE="url_tw.txt"

python3 utils/crawl_url.py \
    --item-selector "$ITEM_SELECTOR" \
    --min-date "$MIN_DATE" \
    --max-date "$MAX_DATE" \
    --max-pages "$MAX_PAGES" \
    --output "$OUTPUT_FILE"
