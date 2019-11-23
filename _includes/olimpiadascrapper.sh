#!/bin/bash

__dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 ${__dir}/olimpiadascraper.py
git add -u
git commit -m "Running autoscrapper"
git push
