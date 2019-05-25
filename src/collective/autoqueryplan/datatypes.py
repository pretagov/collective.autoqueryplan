from ZServer.datatypes import ServerFactory
from server import QueryPlanServer


class ClockServerFactory(ServerFactory):
    def __init__(self, section):
        ServerFactory.__init__(self)
        self.period = section.period

    def create(self):
        from server import ClockServer
        from ZServer.AccessLogger import access_logger
        return QueryPlanServer(self.period, access_logger)

