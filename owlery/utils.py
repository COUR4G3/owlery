import importlib


def import_service_class(name):
    module_name, class_name = name.rsplit(".", 1)

    module = importlib.import_module(module_name, "owlery.services")
    cls = getattr(module, class_name)

    return cls
