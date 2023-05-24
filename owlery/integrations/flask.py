import hashlib
import hmac
import typing as t

import click

from flask import Blueprint, Flask, abort, current_app, request
from werkzeug.local import LocalProxy

from ..services import Service, ServiceManager
from ..signals import on_receive_message


class Owlery:
    """Extension for integrating Owlery with Flask."""

    def __init__(self, app: t.Optional[Flask] = None):
        self.default_app = app
        self.default_services = []  # type: ignore

        if app:
            self.init_app(app)

    def init_app(
        self,
        app: Flask,
        url_prefix: str = "/.owlery",
        cli_group: str = "messages",
    ):
        if not hasattr(app, "extensions"):  # pragma: nocover
            app.extensions = {}

        app.extensions["owlery"] = {"services": {}}

        for name, service_cls, defaults in self.default_services:
            self.register(service_cls, name=name, app=app, **defaults)

        app.register_blueprint(blueprint, url_prefix=url_prefix)

    @classmethod
    def _get_manager(cls, name: str):
        try:
            context = current_app.extensions["owlery"]
        except (AttributeError, KeyError):
            raise RuntimeError("owlery not initialized for this application")

        return context[name]  # this should always exist

    @classmethod
    def _get_service(cls, name: str):
        try:
            context = current_app.extensions["owlery"]
        except (AttributeError, KeyError):
            raise RuntimeError("owlery not initialized for this application")

        return context["services"][name]  # this should always exist

    def register(
        self,
        service_cls: t.Type[Service],
        name: t.Optional[str] = None,
        app: t.Optional[Flask] = None,
        **defaults,
    ):
        r"""Register a service or manager from this application.

        :param service_cls: The service or manager to register.
        :param n ame: Name of the service, defaults to ``service_cls.name``.
        :param app: The Flask application to register for.
        :param \*\*defaults: The configuration defaults for the service.

        """
        app = app or current_app or self.default_app

        # ideally this shouldn't be needed, unless someone call it with `app`
        if app and "owlery" not in app.extensions:
            raise RuntimeError("owlery not initialized for this application")

        if not name:
            name = service_cls.name

        if app and issubclass(service_cls, ServiceManager):
            # register a service manager
            options = defaults

            config_key = f"OWLERY_{name.upper()}_"
            options.update(app.config.get_namespace(config_key))

            # find all services name by finding OWLERY_{MANAGER}_{SERVICE}_CLS
            keys = list(options.keys())
            service_names = set()
            for key in keys:
                if not key.endswith("_cls"):
                    continue
                service_name = key.rsplit("_", 1)[0]
                service_names.add(service_name)

            # get all options per service
            services = {}
            for service_name in service_names:
                service_options = {}
                for key in keys:
                    if not key.startswith(f"{service_name}_"):
                        continue

                    service_key = key.strip(f"{service_name}_")
                    service_options[service_key] = options.pop(key)

                services[service_name] = service_options

            manager = service_cls(**options)

            # register services on manager
            for service_name, options in services.items():
                service_cls = options.pop("cls")
                manager.register(service_cls, name=service_name, **options)

            app.extensions["owlery"][name] = manager

            return manager
        elif app and issubclass(service_cls, Service):
            # register a standalone service
            options = defaults

            config_key = f"OWLERY_SERVICES_{name.upper()}_"
            options.update(app.config.get_namespace(config_key))

            service = service_cls(**options)

            app.extensions["owlery"]["services"][name] = service

            return service
        elif issubclass(service_cls, ServiceManager):
            # prepare service to be registered later on `init_app`
            self.default_services.append((name, service_cls, defaults))

            return LocalProxy(
                lambda: self._get_manager(name),  # type: ignore
                unbound_message="owlery not initialized for this application",
            )
        elif issubclass(service_cls, Service):
            # prepare service to be registered later on `init_app`
            self.default_services.append((name, service_cls, defaults))

            return LocalProxy(
                lambda: self._get_service(name),  # type: ignore
                unbound_message="owlery not initialized for this application",
            )


blueprint = Blueprint(
    "_owlery", __name__, cli_group="messages", url_prefix="/.owlery"
)


def _get_service_for_cli(ctx, param, value):
    if "." in value:
        manager, service = value.split(":", 1)
    else:
        manager = "services"
        service = value

    try:
        if manager == "services":
            services = Owlery._get_service(manager)
            service = services[service]
        else:
            manager = Owlery._get_service(manager)
            service = manager.services[service]
    except KeyError:
        raise click.ClickException("Service not found!")

    return service


def _format_line(name, service):
    return f"{name}(cls={service.__class__.__name__})"


@blueprint.cli.command()
def discover():
    """Discover all managers and services available."""
    try:
        context = current_app.extensions["owlery"]
    except (AttributeError, KeyError):
        raise click.ClickException(
            "owlery not initialized for this application"
        )

    for name, manager in context.items():
        if name == "services":
            continue

        click.echo(_format_line(name, manager))

        for name, service in manager.services.items():
            click.echo(f"\t.{_format_line(name, service)}")

        click.echo("")

    for name, service in context["services"].items():
        click.echo(_format_line(name, service))


@blueprint.cli.command()
@click.argument("service", callback=_get_service_for_cli)
@click.option("-l", "--limit", default=100, type=int)
def receive(limit, service):
    """Receive messages from a configured service or manager."""
    if not on_receive_message.has_receivers_for(service):
        raise click.ClickException(
            "No 'on-receive-message' signal receivers for service!"
        )

    count = 0
    for _ in service.receive(limit=limit - count):
        count += 1

    click.echo(f"Receive {count} messages.")


@blueprint.cli.command(context_settings={"allow_unknown_options": True})
@click.argument("service", callback=_get_service_for_cli)
@click.argument("args", type=click.UNPROCESSED)
def send(args, service):
    """Send a message using a configured service or manager."""
    message = service.send(**dict(args))

    if message.status == "error":
        raise click.ClickException(f"Failed to send message: {message.error}")

    click.echo(f"Message {message.status}. (id={message.id})")


def _get_service_for_route(manager, service):
    try:
        if manager == "services":
            services = Owlery._get_service(manager)
            service = services[service]
        else:
            manager = Owlery._get_service(manager)
            service = manager.services[service]
    except KeyError:
        abort(404)

    return service


@blueprint.route("/webhooks/<manager>/<service>/receive", methods=["POST"])
def receive_webhook(manager, service):
    service = _get_service_for_route(manager, service)
    res, status = service.receive_webhook(request)
    return res, status


@blueprint.route("/webhooks/<manager>/<service>/status", methods=["POST"])
def status_callback(manager, service):
    service = _get_service_for_route(manager, service)
    res, status = service.status_callback(request)
    return res, status
