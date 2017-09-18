#!/bin/bash 
source ./config.sh

result_msg=`curl -X GET -u $AUTH --header 'Accept: application/json' ${BASE_URL}/xosapi/v1/core/networks`
echo $result_msg | python -m json.tool
