from __future__ import unicode_literals

from applications.users.models import *
from django.conf import settings
from graphspace.mixins import *
from sqlalchemy import ForeignKeyConstraint, text, Enum, Boolean, event
import graphspace.signals as socket

Base = settings.BASE


# ================== Table Definitions =================== #


class OwnerNotification(IDMixin, TimeStampMixin, EmailMixin, Base):
    __tablename__ = 'owner_notification'

    message = Column(String, nullable=False)
    type = Column(Enum("create", "upload", "update",
                       "delete", name="owner_notification_types"))
    resource = Column(Enum("graph", "layout", "group",
                           name="owner_notification_resource"))
    resource_id = Column(Integer, nullable=False)

    is_read = Column(Boolean, default=False)

    owner_email = Column(String, ForeignKey(
        'user.email', ondelete="CASCADE", onupdate="CASCADE"), nullable=True)
    owner = relationship(
        "User", back_populates="owned_notifications", uselist=False)

    # Used for bulk notifications
    first_created_at = Column(TIMESTAMP, nullable=True)
    is_bulk = Column(Boolean, default=False)

    constraints = ()
    indices = ()

    @declared_attr
    def __table_args__(cls):
        args = cls.constraints + cls.indices
        return args

    def serialize(cls):
        notify = {
            'id': cls.id,
            'message': cls.message,
            'type': cls.type,
            'is_read': cls.is_read,
            'is_email_sent': cls.is_email_sent,
            'resource': cls.resource,
            'resource_id': cls.resource_id,
            'owner_email': cls.owner_email,
            'created_at': cls.created_at.isoformat(),
            'updated_at': cls.updated_at.isoformat()
        }

        if cls.first_created_at is not None:
            notify['first_created_at'] = cls.first_created_at.isoformat()
            notify['message'] = cls.message + ' ' + cls.resource + ' ' + settings.NOTIFICATION_MESSAGE['owner'][cls.type]['bulk'] + '.'
            notify['count_message'] = cls.message
            
        if cls.is_bulk is not None:
            notify['is_bulk'] = cls.is_bulk

        return notify


class GroupNotification(IDMixin, TimeStampMixin, EmailMixin, Base):
    __tablename__ = 'group_notification'

    message = Column(String, nullable=False)
    type = Column(Enum("share", "unshare", "add",
                       "remove", name="group_notification_types"))
    resource = Column(Enum("graph", "layout", "group_member",
                           name="group_notification_resource"))
    resource_id = Column(Integer, nullable=False)
    is_read = Column(Boolean, default=False)

    member_email = Column(String, ForeignKey(
        'user.email', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    group_member = relationship(
        "User", back_populates="group_notifications", uselist=False)

    owner_email = Column(String, nullable=False)

    group_id = Column(Integer, ForeignKey(
        'group.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    group = relationship(
        "Group", back_populates="group_notifications", uselist=False)

    # Used for bulk notifications
    first_created_at = Column(TIMESTAMP, nullable=True)
    is_bulk = Column(Boolean, default=False)

    constraints = ()
    indices = ()

    @declared_attr
    def __table_args__(cls):
        args = cls.constraints + cls.indices
        return args

    def serialize(cls):
        notify = {
            'id': cls.id,
            'message': cls.message,
            'type': cls.type,
            'is_read': cls.is_read,
            'is_email_sent': cls.is_email_sent,
            'resource': cls.resource,
            'resource_id': cls.resource_id,
            'member_email': cls.member_email,
            'owner_email': cls.owner_email,
            'group_id': cls.group_id,
            'created_at': cls.created_at.isoformat(),
            'updated_at': cls.updated_at.isoformat()
        }

        if cls.first_created_at is not None:
            notify['first_created_at'] = cls.first_created_at.isoformat()
            notify['message'] = cls.message + ' ' + cls.resource + ' ' + settings.NOTIFICATION_MESSAGE['group'][cls.type]['bulk'] + '.'
            notify['count_message'] = cls.message

        if cls.is_bulk is not None:
            notify['is_bulk'] = cls.is_bulk

        return notify


@event.listens_for(OwnerNotification, 'after_insert')
def send_owner_notification(mapper, connection, notify):
    socket.send_notification(notification=notify, topic="owner")


@event.listens_for(GroupNotification, 'after_insert')
def send_group_notification(mapper, connection, notify):
    socket.send_notification(notification=notify, topic="group")