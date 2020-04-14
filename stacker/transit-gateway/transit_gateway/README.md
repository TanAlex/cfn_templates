# transit_gateway

> Note, this has been written initially in CloudFormation as troposphere did not support Transit Gateway at the time of creation. To have a successful deployment, this MUST be deployed with stacker to coordinate the required hooks.

## Caveats

- The __hub__ account that hosts the Transit Gateway needs to be deployed first
- Once the hub account is deployed and RAM share created, the Transit Gateway ID needs to be added to the config to be passed to the __spoke__ accounts
- The spoke accounts will accept the RAM share via a hook but if the share does not exist, the deployment will fail
- only tested using accounts that are not in the same organization
- has not been tested as a remote module

## Usage

1. Deploy `transit_gateway.yaml` to the hub account.
2. Get the Transit Gateway ID.
3. Deploy `transit_gateway_attachment.yaml` in all spoke accounts.
4. In the hub account, manually accept all attachment requests.

## Templates

### transit_gateway.yaml

Creates a Transit Gateway and associates it with a VPC. Shares Transit Gateway resource among Principal accounts.

#### Parameters

- HubAccountId: `String` Account ID where the Transit Gateway will be hosted.
    - used in a condition to not deploy resources to spoke accounts
- VpcId: `String` VPC to be attached to the Transit Gateway.
- SubnetIds: `CommaDelimitedList` One subnet per AZ to route traffic through the Transit Gateway.
- TransitGatewayName: `String` (Optional) provide a name for the Transit Gateway.
    - standard _CAE_ format used if not provided
- AttachmentName: `String` (optional) Name to use for the Transit Gateway VPC attachment.
    - standard _CAE_ format used if not provided
- AutoAcceptSharedAttachments: `String` Indicates whether attachment requests are automatically accepted.
    - defaults to `enable`
- DefaultRouteTableAssociation:`String` Enable or disable automatic association with the default association route table.
    - defaults to `enable`
- DefaultRouteTablePropagation: `String` Enable or disable automatic propagation of routes to the default propagation route table.
    - defaults to `enable`
- DnsSupport: `String` Enable or disable DNS support.
    - defaults to `enable`
- Principals: `CommaDelimitedList` Account IDs to share Transit Gateway with.
#### Outputs

- TransitGateway: ID of the transit gateway.
    - Export: ${AWS::StackName}-TransitGateway
- TransitGatewayRAM: ID of the transit gateway RAM.
    - Export: ${AWS::StackName}-TransitGatewayRAM

### transit_gateway_vpc_attachment.yaml

Associates a VPC with a Transit Gateway.

#### Parameters

- VpcId: `String` VPC to be attached to the Transit Gateway.
- SubnetIds: `CommaDelimitedList` One subnet per AZ to route traffic through the Transit Gateway.
- TransitGatewayId: `String` ID of the TransitGateway.
- AttachmentName: `String` (optional) Name to use for the Transit Gateway VPC attachment.
    - standard _CAE_ format used if not provided
