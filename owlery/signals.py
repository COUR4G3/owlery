from blinker import Namespace

ns = Namespace()

on_after_send = ns.signal("on-after-send")
on_close_session = ns.signal("on-close-session")
on_before_send = ns.signal("on-before-send")
on_open_session = ns.signal("on-open-session")
on_receive_message = ns.signal("on-receive-message")
on_receive_status_callback = ns.signal("on-receive-status-callback")
on_register_service = ns.signal("on-register-service")
on_unregister_service = ns.signal("on-unregister-service")
