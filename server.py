import sys

import raft_pb2 as pb
import raft_pb2_grpc as grpc


class ServerConfig:
    def __init__(self, id: int, address: str, port: int) -> None:
        self.id = id
        self.address = address
        self.port = port

    def __str__(self) -> str:
        return str(self.id) + " " + self.address + " " + str(self.port)


def parse_server_config(config: str) -> ServerConfig:
    params = config.split()
    return ServerConfig(int(params[0]), params[1], int(params[2]))


node_id = sys.argv[1]
servers = []
config_file = open("config.conf", "r")
servers = list(map(parse_server_config, config_file.read().splitlines()))
config_file.close()


class RaftElectionService(grpc.RaftElectionServiceServicer):
    def RequestVote(self, request, context):
        raft_pb2
        return super().RequestVote(request, context)

    def AppendEntries(self, request, context):
        return super().AppendEntries(request, context)

    def GetLeader(self, request, context):
        return super().GetLeader(request, context)

    def Suspend(self, request, context):
        return super().Suspend(request, context)