#!/bin/bash

source ./config.sh

DATA=$(cat <<EOF 
{
    "updated": null,
    "enacted": null,
    "policed": null,
    "backend_register": "",
    "backend_need_delete": false,
    "backend_need_reap": false,
    "backend_status": "",
    "deleted": false,
    "write_protect": false,
    "lazy_blocked": false,
    "no_sync": false,
    "no_policy": false,
    "policy_status": "",
    "name": "",
    "subnet": "",
    "start_ip": "",
    "end_ip": "",
    "ports": "",
    "labels": "",
    "permit_all_slices": false,
    "autoconnect": false,
    "template": null,
    "owner": null
}
EOF
)


curl -H "Accept: application/json; indent=4" -H "Content-Type: application/json" -u $AUTH -X POST -d "$DATA" $HOST/api/tenant/listeners/



