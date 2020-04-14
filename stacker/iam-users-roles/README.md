# stacker/modules/dfs_iam

Creates IAM Resources for Diamond Fulfillment Solutions

## dfs_users_and_roles

Creates DFS IAM Users, Default Group, Admin Group, and Admin Role in Master Account.

Creates Admin Role in non-Master Accounts.

### Usage

A variable number of users can be created by setting the User list variable.

Example: 

```yaml
  users-and-roles:
    class_path: dfs_iam.blueprints.dfs_users_and_roles.BlueprintClass
    variables:
      MasterAccountId: <Account ID>
      DefaultRegion: <Region>
      Users:
        - name: user1@example.com
          group: admin
        - name: user2@example.com
          group: admin
```
By default, users will added to the Default Group. Users can also be added to the admin
group by setting admin for the group variable, as shown above. 

Once an admin user activates MFA, they will be allowed to assume the Admin Roles in
each DFS account.
