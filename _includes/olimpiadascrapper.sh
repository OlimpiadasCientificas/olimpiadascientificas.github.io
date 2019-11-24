#!/bin/bash

__dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd ${__dir}
python3 ${__dir}/olimpiadascraper.py
git pull --rebase
git add -u
git commit -m "Running autoscrapper"
git push
