import logging
from service_manager import ServiceManager
from utils.config import validate_args_from_config

logging.basicConfig()


def main():

    config = validate_args_from_config()
    service_manager = ServiceManager()

    service_manager.execute_service(config)


if __name__ == "__main__":
    main()
