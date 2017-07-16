from channels import Group

from json import dumps
from graphspace.utils import websocket_group_name


def send_notification(topic, notification):
    if topic == 'owner':
        group_name = websocket_group_name(notification['owner_email'])
        notification['topic'] = 'owner'
        Group(group_name).send({'text': dumps(notification)})
    elif topic == 'group':
    	group_name = 'group-' + str(notification['group_id'])
    	notification['topic'] = 'group'
    	Group(group_name).send({'text': dumps(notification)})
