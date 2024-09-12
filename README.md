# AWS External Attack Surface Collector

This script collects various AWS resource endpoints across multiple AWS services and writes them to an Excel file. The collected resources include Route 53 DNS 
records, API Gateway endpoints, Lambda functions, AppSync endpoints, CloudFront distributions, Amplify apps, Elastic Load Balancers (ELB), RDS instances, and EC2 instances.

## Features

- Collects the following AWS resource endpoints:
  - Route 53 DNS records
  - API Gateway endpoints
  - Lambda function URLs
  - AppSync endpoints
  - CloudFront distributions and alternate domain names
  - Amplify app branch URLs
  - Elastic Load Balancer (ELB) endpoints
  - RDS instance endpoints
  - EC2 public IP addresses and DNS names (only those with public IPs)

- Writes the collected data to an Excel file with sheets for each resource type.
- The Excel file is named using the AWS account ID and a timestamp.

## TO-DO
- Will collect the following AWS resource endpoints:
  - Redshift cluster endpoints
  - Elastic Beanstalk endpoints
  
## Requirements

- Python 3.x
- `boto3`
- `pandas`
- `openpyxl`

## Installation

1. Clone the repository or download the script.

2. Create a virtual environment and activate it:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1. Ensure that your AWS credentials are configured. You can use the AWS CLI to configure your credentials:
    ```bash
    aws configure
    ```

2. Run the script:
    ```bash
    python external-assets.py
    ```

