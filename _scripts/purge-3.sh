#!/bin/bash
#
# sh _scripts/purge-3.sh
#


# We now are only going to snapshot nfts every 3 days. This removes past daily snapshots

find . -name "*.json" -type f -print0 | while IFS= read -r -d $'\0' line; do
    # ./rektbulls/2024_May_08.json
    # echo $line

    datetime=$(echo $line | grep -oP '\d{4}_\w{3}_\d{2}')

    last_digits=$(echo $datetime | grep -oP '\d{2}$')

    # if the last digits after _ is not divisible by 3, remove it
    if [ $((10#$last_digits % 3)) -ne 0 ]; then
        rm $line
    fi
done