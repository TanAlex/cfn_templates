# tgw_hooks

## resource_access_manager

### unshare_transit_vpc

**Type: pre_destroy**

Deletes a share.

#### args

- share_name: value to name the share. will default to `transit-gateway-share`

### accept_share

**Type: pre_build**

Accepts a RAM share.

#### args

- accept_from_accounts: (list) account ids to accept share from

### attach_customer_gateway_to_transit_gateway

**Type: post_build**

If customer gateway exists and attachment does not exist, attaches customer gateway to transit gateway.

#### args

- customer_gateway_id
- transit_gateway_id 
