import json, boto3, os, time
from urllib import request, parse

subscription_table = os.environ['subscription_table']
slack_token_parameter_name = os.environ['slack_token_parameter_name']

client = boto3.client('dynamodb')
ssm_client = boto3.client('ssm')

ssm_response = ssm_client.get_parameter(Name=slack_token_parameter_name, WithDecryption=True)

def send_slack_invite(email):
    slack_token = ssm_response["Parameter"]["Value"]
    form_payload = parse.urlencode({"token": slack_token, "email": email})
    req = request.Request("https://slack.com/api/users.admin.invite", form_payload.encode("ascii"), headers={"Content-Type": "application/x-www-form-urlencoded"})
    resp = request.urlopen(req)
    print(resp.read())
    return True

def save_subscription(email):
    response = client.put_item(
        TableName=subscription_table,
        Item={'email': {'S': email}, 'timestamp': {'N': str(int(time.time()))}, 'Expiration': {'N': str(int(time.time())+31536000)}}
    )
    return True

def handle_post(event, context):

    payload = json.loads(event["body"])
    slack_invited = False
    subscribed = False
    if payload["sendSlackInvite"] == True:
        slack_invited = send_slack_invite(payload["email"])
    if payload["addToSubscribers"] == True:
        subscribed = save_subscription(payload["email"])

    body = {
        "slackInviteSent": slack_invited,
        "subscribed": subscribed
    }

    response = {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": 'https://pioco.fi',
            "Access-Control-Allow-Credentials": 'true'
        },
        "body": json.dumps(body)
    }

    return response
