import json
import boto3
import os

cognito_client = boto3.client('cognito-idp')
USER_POOL_ID = os.environ['USER_POOL_ID']

DEFAULT_CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,OPTIONS'
}

def handler(event, context):
    http_method = event['httpMethod']
    if http_method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': DEFAULT_CORS_HEADERS,
            'body': json.dumps({'message': 'CORS preflight successful'})
        }

    claims = event['requestContext']['authorizer']['claims']
    groups = claims.get('cognito:groups', [])

    if 'admin' not in groups:
        return {
            'statusCode': 403,
            'body': json.dumps({'error': 'Unauthorized. Only admins can list users.'}),
            'headers': {
                'Access-Control-Allow-Origin': '*' 
            }
        }

    try:
        response = cognito_client.list_users(
            UserPoolId=USER_POOL_ID
        )
        
        users = []
        for user in response['Users']:
            user_attributes = {attr['Name']: attr['Value'] for attr in user['Attributes']}
            
            # Get user groups
            user_groups_response = cognito_client.admin_list_groups_for_user(
                Username=user['Username'],
                UserPoolId=USER_POOL_ID
            )
            groups_list = [group['GroupName'] for group in user_groups_response['Groups']]

            users.append({
                'username': user['Username'],
                'attributes': user_attributes,
                'enabled': user['Enabled'],
                'userStatus': user['UserStatus'],
                'groups': groups_list
            })

        return {
            'statusCode': 200,
            'body': json.dumps(users),
            'headers': {
                'Access-Control-Allow-Origin': '*'
            }
        }
    except Exception as e:
        print(f"Error listing users: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': {
                'Access-Control-Allow-Origin': '*'
            }
        } 