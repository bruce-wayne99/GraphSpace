from sqlalchemy import and_, desc, asc, func, case, cast
from sqlalchemy.orm import joinedload, subqueryload
from datetime import datetime

from applications.notifications.models import *
from applications.users.models import *
import applications.users.dal as db_users
from graphspace.wrappers import with_session
from graphspace import utils


@with_session
def add_owner_notification(db_session, message, type, resource, resource_id, owner_email=None, is_read=False, is_email_sent=False):
    """
    Add a new owner notification.

    :param db_session: Database session.
    :param message: Message of the notification.
    :param type: Type of the notification.
    :param resource: Resource type (graph,layout,group) of this notification.
    :param resource_id: Resource ID the notification is related to.
    :param owner_email: Email of the notification's owner.
    :param is_read: Check if notification is read or not.
    :param is_email_sent: Check if email has been sent for the notification or not.
    :return: OwnerNotification
    """
    similar_notify = db_session.query(OwnerNotification).filter(
        OwnerNotification.owner_email.ilike(owner_email), OwnerNotification.is_bulk.is_(True))

    prev_notify_query = similar_notify.order_by(
        desc(OwnerNotification.created_at)).first()

    session_commands = []

    if prev_notify_query is not None:
        prev_notify = utils.serializer(prev_notify_query)
        # Check if the last notification is of same type and resource as
        # current one
        if prev_notify['type'] == type and prev_notify['resource'] == resource:
            # Check if last notification is a bulk notification or a normal
            # one; Instead of having another attribute for this we use
            # first_created_at as a check

            notify = OwnerNotification(message=message, type=type, resource=resource, resource_id=resource_id,
                                       owner_email=owner_email, is_read=is_read, is_email_sent=is_email_sent)

            if prev_notify.get('first_created_at', None) is None:
                bulk_notify = OwnerNotification(message='2',
                                                type=type,
                                                resource=resource,
                                                resource_id=resource_id,
                                                owner_email=owner_email,
                                                is_read=is_read,
                                                is_email_sent=is_email_sent,
                                                is_bulk=True,
                                                first_created_at=datetime.strptime(prev_notify['created_at'], "%Y-%m-%dT%H:%M:%S.%f"))
            else:
                bulk_notify = OwnerNotification(message=str(int(prev_notify['message']) + 1),
                                                type=type,
                                                resource=resource,
                                                resource_id=resource_id,
                                                owner_email=owner_email,
                                                is_read=is_read,
                                                is_email_sent=is_email_sent,
                                                is_bulk=True,
                                                first_created_at=datetime.strptime(prev_notify['first_created_at'], "%Y-%m-%dT%H:%M:%S.%f"))

                delete_query = db_session.query(OwnerNotification).filter(
                    OwnerNotification.id == prev_notify['id']).delete(synchronize_session=False)

            similar_notify = similar_notify.filter(OwnerNotification.type == type, OwnerNotification.resource == resource).update({
                'is_bulk': False}, synchronize_session=False)

            session_commands = [notify, bulk_notify]

        else:
            notify = OwnerNotification(message=message, type=type, resource=resource, resource_id=resource_id,
                                       owner_email=owner_email, is_read=is_read, is_email_sent=is_email_sent, is_bulk=True)

            session_commands = [notify]

    else:
        notify = OwnerNotification(message=message, type=type, resource=resource, resource_id=resource_id,
                                   owner_email=owner_email, is_read=is_read, is_email_sent=is_email_sent, is_bulk=True)
        session_commands = [notify]

    db_session.add_all(session_commands)

    return notify


@with_session
def add_group_notification(db_session, message, type, resource, resource_id, group_id, owner_email=None, is_read=False, is_email_sent=False):
    """
    Add a new group notification.

    :param db_session: Database session.
    :param message: Message of the notification.
    :param type: Type of the notification.
    :param resource: Resource type (graph,layout,group) of this notification.
    :param resource_id: Resource ID the notification is related to.
    :param group_id: ID of the notification's group.
    :param owner_email: Email of user who created the notification.
    :param is_read: Check if notification is read or not.
    :param is_email_sent: Check if email has been sent for the notification or not.
    :return: list of GroupNotification
    """

    group_members = db_users.get_users_by_group(
        db_session=db_session, group_id=group_id)

    notify = []
    for mem in group_members:
        notify.append(GroupNotification(message=message, type=type, resource=resource, resource_id=resource_id,
                                        member_email=mem.email, group_id=group_id, owner_email=owner_email, is_read=is_read, is_email_sent=is_email_sent))

    if resource == 'group_member' and type == 'remove':
        group_member = utils.serializer(
            db_users.get_user_by_id(db_session, resource_id))
        notify.append(GroupNotification(message="You were removed from this group.", type=type, resource=resource, resource_id=resource_id, group_id=group_id,
                                        owner_email=owner_email, is_read=is_read, is_email_sent=is_email_sent, member_email=group_member.get('email', None)))

    # db_session.bulk_save_objects(notify)
    db_session.add_all(notify)
    return notify


@with_session
def get_notification_count(db_session, owner_email, is_read=None):
    owner_query = db_session.query(OwnerNotification).filter(
        OwnerNotification.owner_email.ilike(owner_email), OwnerNotification.is_bulk.is_(True))
    group_query = db_session.query(GroupNotification).filter(
        GroupNotification.member_email.ilike(owner_email), OwnerNotification.is_bulk.is_(True))

    if is_read is not None:
        owner_query = owner_query.filter(
            OwnerNotification.is_read.is_(is_read))
        group_query = group_query.filter(
            GroupNotification.is_read.is_(is_read))

    return owner_query.count() + group_query.count()


@with_session
def find_owner_notifications(db_session, owner_email, is_read, limit, offset, is_bulk=True, created_at=None, first_created_at=None, resource=None, type=None):

    query = db_session.query(OwnerNotification).filter(OwnerNotification.is_bulk.is_(
        is_bulk)).order_by(desc(OwnerNotification.created_at))

    if owner_email is not None:
        query = query.filter(OwnerNotification.owner_email.ilike(owner_email))

    if is_read is not None:
        query = query.filter(OwnerNotification.is_read.is_(is_read))

    if created_at is not None and first_created_at is not None and resource is not None and type is not None:
        query = query.filter(OwnerNotification.created_at <= datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%f"),
                             OwnerNotification.created_at >= datetime.strptime(
                                 first_created_at, "%Y-%m-%dT%H:%M:%S.%f"),
                             OwnerNotification.resource == resource,
                             OwnerNotification.type == type)

    total = query.count()

    if offset is not None and limit is not None:
        query = query.limit(limit).offset(offset)

    return total, query.all()


@with_session
def find_group_notifications(db_session, member_email, group_id, is_read, limit, offset, is_bulk=False, created_at=None, first_created_at=None, resource=None, type=None):

    if is_bulk:
        # Get all notification without merging similar notifications into 1
        cte_query = db_session.query(GroupNotification)

        if created_at is not None and first_created_at is not None and resource is not None and type is not None:
            cte_query = cte_query.filter(GroupNotification.created_at <= datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%f"),
                                         GroupNotification.created_at >= datetime.strptime(
                first_created_at, "%Y-%m-%dT%H:%M:%S.%f"),
                GroupNotification.resource == resource,
                GroupNotification.type == type)
    else:
        # Get notifications by merging similar ones
        cte_query = db_session.query(GroupNotification.id,
                                     GroupNotification.message,
                                     GroupNotification.type,
                                     GroupNotification.resource,
                                     case([(GroupNotification.is_read, 1)],
                                          else_=0).label('is_read'),
                                     GroupNotification.owner_email,
                                     GroupNotification.member_email,
                                     GroupNotification.created_at,
                                     GroupNotification.group_id,
                                     (func.row_number().over(order_by=desc(GroupNotification.created_at)) - func.row_number().over(partition_by=GroupNotification.type, order_by=desc(GroupNotification.created_at))).label('row_number'))

    cte_query = cte_query.filter(GroupNotification.member_email.ilike(member_email),
                                 GroupNotification.group_id == group_id)
    
    if is_read is not None:
        cte_query = cte_query.filter(GroupNotification.is_read.is_(is_read))

    if is_bulk:
        query = cte_query.order_by(desc(GroupNotification.created_at))
    else:
        cte_query = cte_query.cte('group_notification_cte')

        query = db_session.query(func.max(cte_query.c.id).label('id'),
                                 case([(func.count(cte_query.c.member_email) > 1,
                                        cast(func.count(cte_query.c.member_email), String))], else_=func.max(cte_query.c.message)).label('message'),
                                 case([(func.count(cte_query.c.member_email) > 1, True)],
                                      else_=False).label('is_bulk'),
                                 cte_query.c.type.label('type'),
                                 cte_query.c.resource.label('resource'),
                                 func.max(cte_query.c.owner_email).label(
                                     'owner_email'),
                                 func.max(cte_query.c.member_email).label(
                                     'member_email'),
                                 func.max(cte_query.c.group_id).label(
                                     'group_id'),
                                 func.max(cte_query.c.created_at).label(
                                     'created_at'),
                                 func.min(cte_query.c.created_at).label(
                                     'first_created_at'),
                                 func.max(cte_query.c.is_read))\
            .group_by(cte_query.c.type, cte_query.c.row_number, cte_query.c.resource, cte_query.c.owner_email)\
            .order_by(desc(func.max(cte_query.c.created_at)))

    total = query.count()

    if offset is not None and limit is not None:
        query = query.limit(limit).offset(offset)

    return total, query.all()


@with_session
def read_owner_notifications(db_session, owner_email, resource=None, type=None, created_at=None, first_created_at=None, notification_id=None):
    query = db_session.query(OwnerNotification)
    query = query.filter(OwnerNotification.owner_email.ilike(owner_email))
    notify = None

    if notification_id is not None:
        query = query.filter(OwnerNotification.id == notification_id)
        notify = query.one_or_none()
        serialized_notify = utils.serializer(notify)
        bulk_notify_query = db_session.query(OwnerNotification).filter(OwnerNotification.owner_email.ilike(owner_email),
                                                                       OwnerNotification.type == serialized_notify[
                                                                           'type'],
                                                                       OwnerNotification.resource == serialized_notify[
                                                                           'resource'],
                                                                       OwnerNotification.is_bulk.is_(
                                                                           True),
                                                                       OwnerNotification.is_read.is_(
                                                                           False),
                                                                       OwnerNotification.created_at >= datetime.strptime(
                                                                           serialized_notify['created_at'], "%Y-%m-%dT%H:%M:%S.%f"),
                                                                       OwnerNotification.first_created_at != None,
                                                                       OwnerNotification.first_created_at <= datetime.strptime(
                                                                           serialized_notify['created_at'], "%Y-%m-%dT%H:%M:%S.%f")
                                                                       )
        bulk_notify = bulk_notify_query.one_or_none()
        if bulk_notify is not None:
            bulk_notify = utils.serializer(bulk_notify)
            total_unread_notify = db_session.query(OwnerNotification).filter(OwnerNotification.owner_email.ilike(owner_email),
                                                                             OwnerNotification.type == bulk_notify[
                                                                                 'type'],
                                                                             OwnerNotification.resource == bulk_notify[
                                                                                 'resource'],
                                                                             OwnerNotification.is_read.is_(
                                                                                 False),
                                                                             OwnerNotification.created_at < datetime.strptime(
                                                                                 bulk_notify['created_at'], "%Y-%m-%dT%H:%M:%S.%f"),
                                                                             OwnerNotification.created_at >= datetime.strptime(
                                                                                 bulk_notify['first_created_at'], "%Y-%m-%dT%H:%M:%S.%f")
                                                                             ).count()
            if total_unread_notify <= 1:
                bulk_notify_query = bulk_notify_query.update(
                    {'is_read': True}, synchronize_session=False)

    else:
        if resource is not None:
            query = query.filter(OwnerNotification.resource == resource)

        if type is not None:
            query = query.filter(OwnerNotification.type == type)

        if created_at is not None:
            query = query.filter(OwnerNotification.created_at <= datetime.strptime(
                created_at, "%Y-%m-%dT%H:%M:%S.%f"))

        if first_created_at is not None:
            query = query.filter(OwnerNotification.created_at >= datetime.strptime(
                first_created_at, "%Y-%m-%dT%H:%M:%S.%f"))

    query = query.filter(OwnerNotification.is_read.is_(False))
    total = query.count()
    query = query.update({'is_read': True}, synchronize_session=False)

    return total, notify


@with_session
def read_group_notifications(db_session, member_email, group_id=None, resource=None, type=None, created_at=None, first_created_at=None, notification_id=None):
    query = db_session.query(GroupNotification)
    query = query.filter(GroupNotification.member_email.ilike(member_email))
    notify = None

    if notification_id is not None:
        query = query.filter(GroupNotification.id == notification_id)
        notify = query.one_or_none()
    else:
        if group_id is not None:
            query = query.filter(GroupNotification.group_id == group_id)

        if resource is not None:
            query = query.filter(GroupNotification.resource == resource)

        if type is not None:
            query = query.filter(GroupNotification.type == type)

        if created_at is not None:
            query = query.filter(GroupNotification.created_at <= datetime.strptime(
                created_at, "%Y-%m-%dT%H:%M:%S.%f"))

        if first_created_at is not None:
            query = query.filter(GroupNotification.created_at >= datetime.strptime(
                first_created_at, "%Y-%m-%dT%H:%M:%S.%f"))

    query = query.filter(GroupNotification.is_read.is_(False))
    total = query.count()
    query = query.update({'is_read': True}, synchronize_session=False)

    return total, notify


# Get notification count per group for all groups
@with_session
def get_notification_count_per_group(db_session, member_email, is_read=None):

    # Get notifications by merging similar ones
    cte_query = db_session.query(GroupNotification.type,
                                 GroupNotification.resource,
                                 GroupNotification.is_read,
                                 GroupNotification.member_email,
                                 GroupNotification.created_at,
                                 GroupNotification.group_id,
                                 (func.row_number().over(order_by=desc(GroupNotification.created_at)) - func.row_number().over(partition_by=GroupNotification.type, order_by=desc(GroupNotification.created_at))).label('row_number'))

    cte_query = cte_query.filter(
        GroupNotification.member_email.ilike(member_email))

    if is_read is not None:
        cte_query = cte_query.filter(GroupNotification.is_read.is_(is_read))

    cte_query = cte_query.cte('group_notification_sub_count_cte')

    query = db_session.query(cte_query.c.type.label('type'),
                             cte_query.c.resource.label('resource'),
                             cte_query.c.group_id.label('group_id')) \
        .group_by(cte_query.c.type, cte_query.c.row_number, cte_query.c.resource, cte_query.c.group_id) \
        .order_by(desc(func.max(cte_query.c.created_at)))

    total = query.count()
    query = query.cte('group_notification_count_cte')

    subquery = db_session.query(
        query.c.group_id.label('group_id'), func.count(query.c.group_id).label('count'))

    subquery = subquery.group_by(query.c.group_id).subquery()

    new_query = db_session.query(Group, subquery.c.count).join(
        subquery, subquery.c.group_id == Group.id).order_by(subquery.c.count.desc())

    return total, new_query.all()

    """
    subquery = db_session.query(GroupNotification.group_id, func.count(
        GroupNotification.group_id).label('count'))
    subquery = subquery.filter(GroupNotification.member_email.ilike(
        member_email))
    total_query = db_session.query(GroupNotification).filter(
        GroupNotification.member_email.ilike(member_email))

    if is_read is not None:
        subquery = subquery.filter(GroupNotification.is_read.is_(is_read))
        total_query = total_query.filter(
            GroupNotification.is_read.is_(is_read))

    subquery = subquery.group_by(GroupNotification.group_id).subquery()

    query = db_session.query(Group, subquery.c.count).join(
        subquery, subquery.c.group_id == Group.id).order_by(subquery.c.count.desc())

    total = total_query.count()
    return total, query.all()
    """
