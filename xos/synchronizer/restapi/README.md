# Pre-requisite
## Make neutron network and subnet with kuryr
## Run following command:
```
xos-deploy
```

# Create New Network 
Run following shell script:
(This example script uses REST API)
```
# add_slice_kuryr-net.sh    # new slice for kuryr network
add_networktemplate.sh    # new network template with kuryr network plug-in
add_network.sh            # new kuryr network
# add_networkslice.sh   # Temporary
lb-test   # To create new service, slice
```

# Create LB Service
Please read LBaaS REST API Documents (README.md)
  https://github.com/sonaproject/lbaas/blob/master/xos/restapi_lbaas/README.md
