# Pre-requisite
## Make neutron network and subnet with kuryr
## Run following command:
```
xos-deploy
lb-test   # To create new service, slice
```

# Create New Network 
Run following shell script:
(This example script uses REST API)
```
add_networktemplate.sh    # new network template with kuryr network plug-in
add_network.sh            # new kuryr network
```

# Create LB Service
Please read LBaaS REST API Documents (README.md)

