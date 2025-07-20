from services.service_retail import ServiceRetail


class ServiceManager:
    def get_service(self, service_name):
        if service_name == "retail":
            return ServiceRetail()
        else:
            raise ValueError("Unknown service: {}".format(service_name))

    def execute_service(self, config):
        service = self.get_service(config["service"])

        service.execute(config)
