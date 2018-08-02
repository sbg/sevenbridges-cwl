#!/usr/bin/env bash

get_metadata () {
    echo $(cat input.json | jq -r ".${1}.metadata.${2}")
}

export -f get_metadata