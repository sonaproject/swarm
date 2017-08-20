#!/bin/bash

source ./config.sh

DATA=$(cat <<EOF 
{ 
    "description": "This is LB as a Service 11:54",
    "enabled": true,
    "name": "lbaas",
    "versionNumber": "v0.9",
    "published": true,
    "view_url": "/admin/lbaas/lbaas/$id$/",
    "icon_url": "",
    "public_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDvvm6eMJ7qGtrzBn3E5OrYpzejaVEdLHi+sTdioI45Ch1b+UHcS6383+BzQ7xNSae+B7wEVzmBEBl8aqQwTUrkXr+763+C22rQ7Vud47OWBb8LmTrxNzDoayIxcBw8KjAHv0gFW03vuZumRyVqi745RZkxvmw6UCmJbXlHecc31HwKIOnVSgdeWOrJabejRw+cyMsBboPI7qRpotPFn7DaB0hpdAM6PexzrucUS1qynKyH0Zs4XlKiTURpSCrqVpQyVibhuIUSb0Pt1iaPEKa7gyu0ZaPxjcsvlWTFF0O9QD0oGBJQFViBxiALwxVEJCYlDm3vEXTl2NnUJ1PbWcIjXLd6tCdUjjaqVcUrbeTHQTeKbBlLQnWpsPFUhlo9M5gR2ALxU+Cd5w7CT2LKSK3YxWFxwrYIlTecufAWA1hMyQFUsbs5LMBxMSuKdG5muD321ajRo7TQmDc7AfrbtnFBnZiUF03GpWFBQGRHNiRXIn2HvFZgjvW9JPGDvk0Q0MsrNA/DGaBPTvuRWXMgHA4fyRA5BufZIu9XTFGIoRkScmflT2rS5kg87fy4sExMCyTBvRMcrhMNbPmCrsvU8kWghJOyxUE2ah4+4IZ7vfQvbc08heyBBdAECK5nOuOywuI83q8zgZy05OMFP2G+2Ylyq6oGc//EDha7LjhSbggtyQ== CORD SSH client keyfor headnode+",
    "private_key_fn": "/opt/xos/services/lbaas/keys/lbaas_rsa",
    "service_specific_id": "",
    "service_specific_attribute": "" 
}
EOF
)

curl -H "Accept: application/json; indent=4" -H "Content-Type: application/json" -u $AUTH -X POST -d "$DATA" $HOST/api/core/services/


