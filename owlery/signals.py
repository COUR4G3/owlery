from blinker import Namespace

ns = Namespace()

on_after_send = ns.signal("on-after-send")
on_close_session = ns.signal("on-close-session")
on_before_send = ns.signal("on-before-send")
on_open_session = ns.signal("on-open-session")
on_receive_message = ns.signal("on-receive-message")
