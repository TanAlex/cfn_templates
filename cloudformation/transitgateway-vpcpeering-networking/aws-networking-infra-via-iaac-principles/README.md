## Using Infrastructure as Code to Manage Your AWS Networking Environment

Infrastructure as Code (IaC) brings automation to the provisioning process, which was traditionally done manually. Rather than relying on manually performed steps, both administrators and developers can instantiate infrastructure using configuration files. IaC helps avoid configuration drift through automation, and increases the speed and agility of infrastructure deployments. It also helps reduce errors and enhances the ability to apply changes through different stages consistently.

In this blog post, I demonstrate how to create a networking stack on AWS using AWS CloudFormation and manage it via IaC concepts and tools. In this blog, we create a pipeline using AWS CodeCommit and AWS CodePipeline services. Once we have created the pipeline and other required constructs to manage the infrastructure as code, we will add an Amazon Managed Virtual Private Network (VPN) connection, Amazon VPC (VPC) Endpoints, VPC peering, and AWS Transit Gateway. We do this by modifying the code instead of making changes from AWS web console. 
  
## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

