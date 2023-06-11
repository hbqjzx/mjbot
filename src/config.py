import argparse
import os


class SimpleConfig:
    def __init__(self):
        attrs = [_attr_name for _attr_name in dir(self) if not _attr_name.startswith("_") and
                 (self.__getattribute__(_attr_name) is None or not callable(self.__getattribute__(_attr_name)))]
        parser = argparse.ArgumentParser()
        for attr in attrs:
            parser.add_argument(f"-{attr}", dest=attr, required=False)
        args = parser.parse_args()

        for attr in attrs:
            final_value = None
            if hasattr(args, attr):
                final_value = getattr(args, attr)
            if final_value is None:
                final_value = os.environ.get(attr.upper())
            if final_value is None:
                final_value = self.__getattribute__(attr)
            self.__setattr__(attr, final_value)


class Config(SimpleConfig):
    log_level = "INFO"
    wechaty_puppet = "wechaty-puppet-service"
    wechaty_puppet_service_token = None
    zhishuyun_chatgpt_35_token = None
    zhishuyun_midjourney_token = None

    def __repr__(self):
        return "Config(%r)" % self.__dict__
