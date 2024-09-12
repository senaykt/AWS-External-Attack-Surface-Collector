import pandas as pd
import boto3
from botocore.exceptions import NoCredentialsError, NoRegionError, ClientError
from datetime import datetime

def get_aws_account_id():
    try:
        sts_client = boto3.client('sts')
        identity = sts_client.get_caller_identity()
        return identity['Account']
    except Exception as e:
        print(f"Unable to get AWS account ID: {e}")
        return None

def list_route53_records(account_id):
    records_data = []
    try:
        session = boto3.Session()
        client = session.client('route53')

        hosted_zones_response = client.list_hosted_zones()
        hosted_zones = hosted_zones_response['HostedZones']

        for zone in hosted_zones:
            zone_id = zone['Id'].split('/')[-1]
            zone_name = zone['Name']

            next_record_name = None
            next_record_type = None
            is_truncated = True

            while is_truncated:
                if next_record_name and next_record_type:
                    record_sets_response = client.list_resource_record_sets(
                        HostedZoneId=zone_id,
                        StartRecordName=next_record_name,
                        StartRecordType=next_record_type
                    )
                else:
                    record_sets_response = client.list_resource_record_sets(HostedZoneId=zone_id)
                
                record_sets = record_sets_response['ResourceRecordSets']

                for record in record_sets:
                    record_name = record['Name']
                    record_type = record['Type']

                    if 'ResourceRecords' in record:
                        record_values = ', '.join([r['Value'] for r in record['ResourceRecords']])
                    elif 'AliasTarget' in record:
                        record_values = record['AliasTarget']['DNSName']
                    else:
                        record_values = 'N/A'

                    records_data.append([account_id, zone_name, record_name, record_type, record_values])

                is_truncated = record_sets_response['IsTruncated']
                if is_truncated:
                    next_record_name = record_sets_response['NextRecordName']
                    next_record_type = record_sets_response['NextRecordType']

    except NoCredentialsError:
        print("No AWS credentials found. Please configure your AWS credentials.")
    except ClientError as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

    return records_data

def get_api_gateway_endpoints(account_id):
    endpoints_data = []
    try:
        session = boto3.Session()
        regions = session.get_available_regions('apigateway')

        for region in regions:
            try:
                client = session.client('apigateway', region_name=region)
                response = client.get_rest_apis()
                apis = response['items']
                
                if apis:
                    for api in apis:
                        api_id = api['id']
                        api_name = api['name']
                        
                        stages_response = client.get_stages(restApiId=api_id)
                        stages = stages_response['item']
                        
                        if stages:
                            for stage in stages:
                                stage_name = stage['stageName']
                                invoke_url = f"https://{api_id}.execute-api.{region}.amazonaws.com/{stage_name}"
                                endpoints_data.append([account_id, region, api_name, api_id, stage_name, invoke_url])
            
            except client.exceptions.ClientError:
                continue
    
    except NoRegionError:
        print("No region found. Please configure your AWS region.")
    except NoCredentialsError:
        print("No AWS credentials found. Please configure your AWS credentials.")
    except Exception as e:
        print(f"An error occurred: {e}")

    return endpoints_data

def get_lambda_functions(account_id):
    lambda_data = []
    try:
        session = boto3.Session()
        regions = session.get_available_regions('lambda')

        for region in regions:
            print(f"Processing region: {region}")
            try:
                client = session.client('lambda', region_name=region)
                next_marker = None
                while True:
                    if next_marker:
                        response = client.list_functions(Marker=next_marker)
                    else:
                        response = client.list_functions()
                    
                    functions = response['Functions']
                    print(f"Found {len(functions)} functions in region {region}")

                    for function in functions:
                        function_name = function['FunctionName']
                        
                        # Get function configuration to retrieve the function URL
                        try:
                            url_config = client.get_function_url_config(FunctionName=function_name)
                            function_url = url_config['FunctionUrl']
                        except client.exceptions.ResourceNotFoundException:
                            function_url = 'N/A'
                        except client.exceptions.AccessDeniedException as e:
                            print(f"Access denied for function {function_name} in region {region}: {e}")
                            function_url = 'AccessDenied'
                        except ClientError as e:
                            print(f"Error getting URL for function {function_name} in region {region}: {e}")
                            function_url = 'Error'
                        
                        if function_url not in ['N/A', 'AccessDenied', 'Error']:
                            lambda_data.append([account_id, region, function_name, function_url])
                            print(f"Processed function: {function_name} in region {region}, URL: {function_url}")
                    
                    next_marker = response.get('NextMarker')
                    if not next_marker:
                        break
            
            except ClientError as e:
                print(f"Error listing functions in region {region}: {e}")
    
    except NoRegionError:
        print("No region found. Please configure your AWS region.")
    except NoCredentialsError:
        print("No AWS credentials found. Please configure your AWS credentials.")
    except Exception as e:
        print(f"An error occurred: {e}")

    return lambda_data

def get_appsync_endpoints(account_id):
    appsync_data = []
    try:
        session = boto3.Session()
        regions = session.get_available_regions('appsync')

        for region in regions:
            print(f"Processing region: {region}")
            try:
                client = session.client('appsync', region_name=region)
                response = client.list_graphql_apis()
                graphql_apis = response['graphqlApis']
                print(f"Found {len(graphql_apis)} GraphQL APIs in region {region}")

                for api in graphql_apis:
                    api_name = api['name']
                    api_url = api['uris'].get('GRAPHQL')

                    if api_url:
                        appsync_data.append([account_id, region, api_name, api_url])
                        print(f"Processed GraphQL API: {api_name} in region {region}, URL: {api_url}")
            
            except ClientError as e:
                print(f"Error listing GraphQL APIs in region {region}: {e}")
    
    except NoRegionError:
        print("No region found. Please configure your AWS region.")
    except NoCredentialsError:
        print("No AWS credentials found. Please configure your AWS credentials.")
    except Exception as e:
        print(f"An error occurred: {e}")

    return appsync_data

def get_cloudfront_endpoints(account_id):
    cloudfront_data = []
    try:
        session = boto3.Session()
        client = session.client('cloudfront')

        response = client.list_distributions()
        distributions = response['DistributionList'].get('Items', [])
        print(f"Found {len(distributions)} distributions")

        for dist in distributions:
            dist_id = dist['Id']
            dist_domain = dist['DomainName']
            dist_name = dist['Origins']['Items'][0]['Id']
            alternate_domain_names = ', '.join(dist.get('Aliases', {}).get('Items', []))

            cloudfront_data.append([account_id, dist_id, dist_name, dist_domain, alternate_domain_names])
            print(f"Processed distribution: {dist_name}, Domain: {dist_domain}, Aliases: {alternate_domain_names}")
    
    except NoCredentialsError:
        print("No AWS credentials found. Please configure your AWS credentials.")
    except ClientError as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

    return cloudfront_data


def get_amplify_endpoints(account_id):
    amplify_data = []
    try:
        session = boto3.Session()
        regions = session.get_available_regions('amplify')

        for region in regions:
            print(f"Processing region: {region}")
            try:
                client = session.client('amplify', region_name=region)
                response = client.list_apps()
                apps = response['apps']
                print(f"Found {len(apps)} apps in region {region}")

                for app in apps:
                    app_id = app['appId']
                    app_name = app['name']
                    default_domain = app.get('defaultDomain', 'N/A')

                    # List branches for the app to get full URLs
                    branch_response = client.list_branches(appId=app_id)
                    branches = branch_response['branches']

                    for branch in branches:
                        branch_name = branch['branchName']
                        branch_url = f"https://{branch_name}.{default_domain}"

                        amplify_data.append([account_id, region, app_id, app_name, branch_name, branch_url])
                        print(f"Processed app: {app_name} in region {region}, Branch: {branch_name}, URL: {branch_url}")
            
            except ClientError as e:
                print(f"Error listing apps in region {region}: {e}")
    
    except NoRegionError:
        print("No region found. Please configure your AWS region.")
    except NoCredentialsError:
        print("No AWS credentials found. Please configure your AWS credentials.")
    except Exception as e:
        print(f"An error occurred: {e}")

    return amplify_data



def get_elb_endpoints(account_id):
    elb_data = []
    try:
        session = boto3.Session()
        regions = session.get_available_regions('elbv2')

        for region in regions:
            print(f"Processing region: {region}")
            try:
                client = session.client('elbv2', region_name=region)
                response = client.describe_load_balancers()
                load_balancers = response['LoadBalancers']
                print(f"Found {len(load_balancers)} load balancers in region {region}")

                for lb in load_balancers:
                    lb_name = lb['LoadBalancerName']
                    lb_dns = lb['DNSName']

                    elb_data.append([account_id, region, lb_name, lb_dns])
                    print(f"Processed load balancer: {lb_name} in region {region}, DNS: {lb_dns}")
            
            except ClientError as e:
                print(f"Error listing load balancers in region {region}: {e}")
    
    except NoRegionError:
        print("No region found. Please configure your AWS region.")
    except NoCredentialsError:
        print("No AWS credentials found. Please configure your AWS credentials.")
    except Exception as e:
        print(f"An error occurred: {e}")

    return elb_data


def get_rds_endpoints(account_id):
    rds_data = []
    try:
        session = boto3.Session()
        regions = session.get_available_regions('rds')

        for region in regions:
            print(f"Processing region: {region}")
            try:
                client = session.client('rds', region_name=region)
                response = client.describe_db_instances()
                db_instances = response['DBInstances']
                print(f"Found {len(db_instances)} RDS instances in region {region}")

                for db_instance in db_instances:
                    db_instance_id = db_instance['DBInstanceIdentifier']
                    db_endpoint = db_instance['Endpoint']['Address']

                    rds_data.append([account_id, region, db_instance_id, db_endpoint])
                    print(f"Processed RDS instance: {db_instance_id} in region {region}, Endpoint: {db_endpoint}")
            
            except ClientError as e:
                print(f"Error listing RDS instances in region {region}: {e}")
    
    except NoRegionError:
        print("No region found. Please configure your AWS region.")
    except NoCredentialsError:
        print("No AWS credentials found. Please configure your AWS credentials.")
    except Exception as e:
        print(f"An error occurred: {e}")

    return rds_data

def get_ec2_endpoints(account_id):
    ec2_data = []
    try:
        session = boto3.Session()
        regions = session.get_available_regions('ec2')

        for region in regions:
            print(f"Processing region: {region}")
            try:
                client = session.client('ec2', region_name=region)
                response = client.describe_instances()
                reservations = response['Reservations']
                print(f"Found {len(reservations)} reservations in region {region}")

                for reservation in reservations:
                    instances = reservation['Instances']
                    for instance in instances:
                        instance_id = instance['InstanceId']
                        public_ip = instance.get('PublicIpAddress')
                        public_dns = instance.get('PublicDnsName', 'N/A')

                        if public_ip:  # Only include instances with a public IP
                            ec2_data.append([account_id, region, instance_id, public_ip, public_dns])
                            print(f"Processed instance: {instance_id} in region {region}, Public IP: {public_ip}, Public DNS: {public_dns}")
            
            except ClientError as e:
                print(f"Error listing instances in region {region}: {e}")
    
    except NoRegionError:
        print("No region found. Please configure your AWS region.")
    except NoCredentialsError:
        print("No AWS credentials found. Please configure your AWS credentials.")
    except Exception as e:
        print(f"An error occurred: {e}")

    return ec2_data



if __name__ == "__main__":
    account_id = get_aws_account_id()
    
    if account_id:
        dns_records_data = list_route53_records(account_id)
        dns_df = pd.DataFrame(dns_records_data, columns=['Account ID', 'Hosted Zone', 'Domain', 'Record Type', 'Record Value'])
        
        api_endpoints_data = get_api_gateway_endpoints(account_id)
        api_df = pd.DataFrame(api_endpoints_data, columns=['Account ID', 'Region', 'API Name', 'API ID', 'Stage', 'Invoke URL'])
        
        lambda_data = get_lambda_functions(account_id)
        print(f"Collected Lambda data: {lambda_data}")  # Debugging line
        lambda_df = pd.DataFrame(lambda_data, columns=['Account ID', 'Region', 'Function Name', 'Function URL'])
        
        appsync_data = get_appsync_endpoints(account_id)
        print(f"Collected AppSync data: {appsync_data}")  # Debugging line
        appsync_df = pd.DataFrame(appsync_data, columns=['Account ID', 'Region', 'API Name', 'API URL'])

        cloudfront_data = get_cloudfront_endpoints(account_id)
        print(f"Collected CloudFront data: {cloudfront_data}")  # Debugging line
        cloudfront_df = pd.DataFrame(cloudfront_data, columns=['Account ID', 'Distribution ID', 'Distribution Name', 'Domain Name', 'Alternate Domain Names'])

        amplify_data = get_amplify_endpoints(account_id)
        print(f"Collected Amplify data: {amplify_data}")  # Debugging line
        amplify_df = pd.DataFrame(amplify_data, columns=['Account ID', 'Region', 'App ID', 'App Name', 'Branch Name', 'Branch URL'])

        elb_data = get_elb_endpoints(account_id)
        print(f"Collected ELB data: {elb_data}")  # Debugging line
        elb_df = pd.DataFrame(elb_data, columns=['Account ID', 'Region', 'Load Balancer Name', 'DNS Name'])

        rds_data = get_rds_endpoints(account_id)
        print(f"Collected RDS data: {rds_data}")  # Debugging line
        rds_df = pd.DataFrame(rds_data, columns=['Account ID', 'Region', 'DB Instance ID', 'Endpoint'])

        ec2_data = get_ec2_endpoints(account_id)
        print(f"Collected EC2 data: {ec2_data}")  # Debugging line
        ec2_df = pd.DataFrame(ec2_data, columns=['Account ID', 'Region', 'Instance ID', 'Public IP', 'Public DNS'])

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"aws_resources_{account_id}_{timestamp}.xlsx"

        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            dns_df.to_excel(writer, sheet_name='Route 53 DNS Records', index=False)
            api_df.to_excel(writer, sheet_name='API Gateway Endpoints', index=False)
            lambda_df.to_excel(writer, sheet_name='Lambda Functions', index=False)
            appsync_df.to_excel(writer, sheet_name='AppSync Endpoints', index=False)
            cloudfront_df.to_excel(writer, sheet_name='CloudFront Distributions', index=False)
            amplify_df.to_excel(writer, sheet_name='Amplify Apps', index=False)
            elb_df.to_excel(writer, sheet_name='ELB Endpoints', index=False)
            rds_df.to_excel(writer, sheet_name='RDS Endpoints', index=False)
            ec2_df.to_excel(writer, sheet_name='EC2 Instances', index=False)
        
        print(f"Data written to {filename}")
    else:
        print("Failed to retrieve AWS account ID.")
