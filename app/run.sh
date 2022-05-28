#!/usr/bin/env bash

set -e

base_dir=$(cd $(dirname $0);pwd)
custom_env=${base_dir}/run.env

logfile=${base_dir}/log/nico-gift-event-graph.log

if [ -e ${custom_env} ]; then
    source ${custom_env}
fi

cd ${base_dir}

./main.py >> ${logfile}