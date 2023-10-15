import typing as t

from flask import Flask, current_app
from werkzeug.local import LocalProxy

from ..services import Service, ServiceManager
from ..utils import import_service_class


class Owlery:
    """Flask integration for the Owlery messaging service."""

    def __init__(self, app: t.Optional[Flask] = None):
        self.default_app = app
        self.default_services: t.Dict[str, t.Dict[str, t.Any]] = {}

        if app:
            self.init_app(app)

    def init_app(self, app: Flask):
        """Initialise the application in an application factory pattern."""
        services: t.Dict[str, Service] = {}

        if not hasattr(app, "extensions"):
            app.extensions = {}
        app.extensions["owlery"] = services

        for name, options in self.default_services.items():
            service = self.register(name, app=app, **options)
            services[name] = service

    def get_app(self, raise_exception=True):
        """Get the current or default application.

        :return: The current or default Flask application.
        :rtype: Flask
        :raises: RuntimeError: No application / request context or default
                               application.

        """
        try:
            return current_app._get_current_object()
        except RuntimeError:
            if self.default_app:
                return self.default_app
            if raise_exception:
                raise

    def get_service(self, name) -> t.Union[Service, ServiceManager]:
        """Get a service by `name`.

        If the service is not yet registered, it will attempt to automatically
        register the service.

        :return: The named service or service manager.
        :rtype: Service | ServiceManager
        :raises: RuntimeError: Service is not registered, configured or no
                               application / request context.

        """
        app = self.get_app()

        try:
            services = app.extensions["owlery"]
        except KeyError:
            raise RuntimeError("Owlery not configured for this application")

        try:
            service = services[name]
        except KeyError:
            try:
                service = self.register(name, app=app)
            except RuntimeError:
                raise KeyError(f"No service named '{name}'")

        return service

    def __getattr__(self, name):
        app = self.get_app(raise_exception=False)

        if app and name in app.extensions["owlery"]:
            return app.extensions["owlery"][name]

        return super().__getattr__(name)

    def __getitem__(self, name):
        app = self.get_app()

        if app and name in app.extensions["owlery"]:
            return app.extensions["owlery"][name]

        raise KeyError(f"No service named '{name}'")

    def register(self, name, app: t.Optional[Flask] = None, **default_options):
        """Register a service.

        The service configuration is obtained by merging ``default_options``
        with options from the Flask application configuration.

        If no current application context and no default application is
        associated with the extension, a proxy object will be returned, which
        can be used when there is an application or request context.

        :return: The named service or service manager, or a proxy to one.
        :rtype: Service | ServiceManager
        :raises: RuntimeError: Service is not configured.

        """
        if not app:
            app = self.get_app(raise_exception=False)
        if not app:
            self.default_services[name] = default_options
            return LocalProxy(
                lambda: self.get_service(name),
                unbound_message="outside of application context",
            )

        options = default_options
        options.update(app.config.get_namespace(f"OWLERY_{name.upper()}_"))

        class_ = options.pop("cls", None)
        if not class_:
            raise RuntimeError(f"Service '{name}' is not configured")

        if isinstance(class_, str):
            class_ = import_service_class(class_)

        service = class_(name=name, **options)

        if issubclass(class_, ServiceManager):
            # is a service manager
            service_names = []
            for key in options:
                if not key.endswith("_cls"):
                    continue
                service_names.append(key.removesuffix("_cls"))

            for service_name in service_names:
                service_cls = options.pop(f"{service_name}_cls")
                if isinstance(service_cls, str):
                    service_cls = import_service_class(service_cls)

                service_opts = {
                    k.removeprefix(f"{service_name}_"): v
                    for k, v in options.items()
                    if k.startswith(f"{service_name}_")
                }
                service.register(
                    service_cls,
                    name=service_name,
                    **service_opts,
                )

        app.extensions["owlery"][name] = service
        return service
