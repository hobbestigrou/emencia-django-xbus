# Import from the Standard Library
from uuid import uuid4
from traceback import format_exc

# Import from Django
from django.conf import settings

# Other
import msgpack
from zmq_rpc.client import ZmqRpcClient

# Import from xbus
from xbus.models import Event


registry = {}


def register_handler(event_type, handler):
    registry[event_type] = handler


def send_event(instance, event_type, item, immediate=False, admin_url=None):
    """
    Utility function used typically by signal handlers to send an xbus event.
    For now we only support sending 1 event per envelop, and 1 item per event.
    """
    # Identify the object and the message
    xbus_message_correlation_id = str(uuid4())

    # If the instance hasn't a xref, we create it
    if not instance.xref:
        instance.xref = str(uuid4())
        instance.save(update_fields=['xref', ])

    xref = str(instance.xref)

    # Fill item
    item['xref'] = xref
    item['xbus_message_correlation_id'] = xbus_message_correlation_id

    # The broker, written in Python 3, expects unicode for everything
    item = {unicode(k): unicode(v) if type(v) is str else v
            for k, v in item.items()}
    event_type = unicode(event_type)

    # Pack
    item = msgpack.packb(item)

    if immediate:
        direction = 'immediate-out'
    else:
        direction = 'out'

    # Add to the queue
    event = Event.objects.create(
        direction=direction,
        state='pending',
        xbus_message_correlation_id=xbus_message_correlation_id,
        xref=xref,
        event_type=event_type,
        item=item,
        admin_url=admin_url,
    )

    if immediate:
        try:
            ret_code, ret_val = send_immediate_reply_event(event)
            event.state = 'done'
            event.comment = (
                "Returned code: %s\nReturned val: %s"
                % (ret_code, ret_val)
            )
            event.save()
            return event, ret_code, ret_val
        except Exception:
            event.state = 'error'
            event.comment = format_exc()
            event.save()
            return event, False, None

    return event


def new_connection_to_xbus():
    front_url = settings.XBUS_EMITTER_URL
    login = settings.XBUS_EMITTER_LOGIN
    password = settings.XBUS_EMITTER_PASSWORD

    conn = ZmqRpcClient(front_url, timeout=1000)
    token = conn.login(login, password)

    if not token:
        raise Exception('Error: Authentication failed.')

    return conn, token


def send_immediate_reply_event(event):
    conn, token = new_connection_to_xbus()
    return _xbus_send_event(conn, token, event)


def _xbus_send_event(conn, token, event):
    event_type = event.event_type
    item = event.item

    # conn.packer.pack != msgpack.packb
    item = msgpack.unpackb(item, encoding='utf-8')
    item = conn.packer.pack(item)

    # Send
    print 'Sending event...', event_type
    envelope_id = conn.start_envelope(token)
    event_id = conn.start_event(token, envelope_id, event_type, 0)

    if not event_id:
        error = (
            "Error: the following event_type isn't registered with "
            "xbus or you might not have the right permissions to send "
            "it: %s" % event_type
        )
        event.state = 'error'
        event.comment = error
        event.save()
        print error
        return None

    conn.send_item(token, envelope_id, event_id, item)
    ret = conn.end_event(token, envelope_id, event_id)
    conn.end_envelope(token, envelope_id)

    return ret
