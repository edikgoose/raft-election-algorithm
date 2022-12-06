import multiprocessing
import random
import sys
import threading
import time
from concurrent import futures
from typing import Callable, Any

import grpc
import raft_pb2
import raft_pb2_grpc as pb_grpc

# noinspection DuplicatedCode
AppendRequest = raft_pb2.AppendRequest
AppendResponse = raft_pb2.AppendResponse
GetLeaderResponse = raft_pb2.GetLeaderResponse
SuspendRequest = raft_pb2.SuspendRequest
Void = raft_pb2.Void
VoteRequest = raft_pb2.VoteRequest
VoteResponse = raft_pb2.VoteResponse
Key = raft_pb2.Key
KeyValue = raft_pb2.KeyValue
SetValResponse = raft_pb2.SetValResponse
GetValResponse = raft_pb2.GetValResponse


HEARTBEAT_INTERVAL = 50  # ms
ELECTION_INTERVAL = 300, 600  # ms


def parse_server_config(config: str) -> (int, str):
    params = config.split()
    return int(params[0]), f"{params[1]}:{params[2]}"


def generate_random_timeout() -> int:
    return random.randint(ELECTION_INTERVAL[0], ELECTION_INTERVAL[1])


def start_after_time(period_sec: float, func: Callable, *args, **kwargs) -> None:
    timer = threading.Timer(period_sec, func, args, kwargs)
    timer.start()


# noinspection PyUnresolvedReferences
class RepeatTimer(threading.Timer):
    """ Taken from https://stackoverflow.com/a/48741004/11825114 """

    def run(self) -> None:
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


class RaftElectionService(pb_grpc.RaftElectionServiceServicer):

    def __init__(self, server_id: int, server_address: str, servers: dict[int, str]) -> None:
        self.current_term = 0
        self.server_id = server_id
        self.server_address = server_address
        self.servers = servers
        self.election_timeout = generate_random_timeout()
        self.state = None
        self.election_timer = None
        self.current_vote = None
        self.start_following()
        self.leader_id = None
        self.leader_address = None
        self.leader_timer = None
        self.should_interrupt = False
        super().__init__()

    def start_election_timer(self) -> threading.Timer:
        """ Unit of timeout is ms """
        election_timer = threading.Timer(self.election_timeout / 1000, self.start_election)
        election_timer.start()
        return election_timer

    def start_following(self):
        self.state = "follower"
        print(f"I am a follower. Term: {self.current_term}")
        self.election_timer = self.start_election_timer()

    def start_election(self):
        print("The leader is dead")
        print(f"I am a candidate. Term: {self.current_term}")
        if self.state != "follower":
            return

        self.state = "candidate"
        self.current_term += 1
        self.current_vote = self.server_id
        print(f"Voted for node {self.server_id}")
        number_of_voted = 1  # because server initially votes for itself

        queue = multiprocessing.Queue()
        threads = []

        for _, server_address in self.servers.items():
            thread = threading.Thread(target=self.request_election_vote, args=(server_address, queue))
            thread.setDaemon(True)
            threads.append(thread)
            if self.state != "candidate":
                return
            thread.start()

        for thread in threads:
            thread.join()

        print(f"Votes received")
        while not queue.empty():
            vote_result = queue.get()
            if vote_result is None:  # if server is not responding
                continue

            if vote_result.term > self.current_term:
                self.current_term = vote_result.term
                self.current_vote = None
                self.start_following()
                return
            if vote_result.result:
                number_of_voted += 1

        if number_of_voted > (len(self.servers) + 1) / 2:
            self.start_leading()
        else:
            self.election_timeout = generate_random_timeout()
            self.start_following()

    def request_election_vote(self, address: str, queue) -> None:
        channel = grpc.insecure_channel(address)
        client_stub = pb_grpc.RaftElectionServiceStub(channel)
        # noinspection PyBroadException
        try:
            result = client_stub.RequestVote(
                VoteRequest(candidateTerm=self.current_term, candidateId=self.server_id))
            queue.put(result)
        except Exception:
            pass

    def start_leading(self):
        print(f"I am a leader. Term: {self.current_term}")
        self.election_timer.cancel()
        self.state = "leader"
        self.leader_id = self.server_id
        self.leader_address = self.server_address

        self.leader_timer = RepeatTimer(HEARTBEAT_INTERVAL / 1000, function=self.send_heartbeats)
        self.leader_timer.start()
        while self.state == "leader":
            if self.should_interrupt:
                self.leader_timer.cancel()
                return
        print(f"I am a follower. Term: {self.current_term}")
        self.leader_timer.cancel()

    def send_heartbeats(self):
        threads = []

        for _, server_address in self.servers.items():
            thread = threading.Thread(target=self.send_heartbeat, args=(server_address,))
            thread.setDaemon(True)
            threads.append(thread)
            thread.start()

        for thread in threads:
            if self.should_interrupt:
                return
            thread.join()

    def send_heartbeat(self, server_address):
        channel = grpc.insecure_channel(server_address)
        client_stub = pb_grpc.RaftElectionServiceStub(channel)
        # noinspection PyBroadException
        try:
            result = client_stub.AppendEntries(
                AppendRequest(leaderTerm=self.current_term, leaderId=self.server_id))
            if not result.success:
                self.current_term = result.term
                self.state = "follower"
                return
        except Exception:
            pass

    def RequestVote(self, request, context):
        if request.candidateTerm > self.current_term or \
                (request.candidateTerm == self.current_term and
                 (self.current_vote is None or self.current_vote == request.candidateId)):
            self.current_term = request.candidateTerm
            self.current_vote = request.candidateId
            if self.state != "follower":
                self.start_following()
            return VoteResponse(term=self.current_term, result=True)
        else:
            return VoteResponse(term=self.current_term, result=False)

    def AppendEntries(self, request: AppendRequest, context):
        try:
            if self.state == "follower":
                self.election_timer.cancel()
                self.election_timer = self.start_election_timer()

            self.leader_id = request.leaderId
            self.leader_address = self.servers[request.leaderId]

            if request.leaderTerm >= self.current_term:
                self.current_term = request.leaderTerm
                return AppendResponse(term=self.current_term, success=True)
            else:
                return AppendResponse(term=self.current_term, success=False)
        except grpc.RpcError as e:
            print(str(e))

    def GetLeader(self, request, context):
        print("Command from client: getleader")
        node_id, node_address = None, None

        if self.state == "candidate":
            if not self.current_vote:
                node_id, node_address = self.current_vote, self.servers[self.current_vote]
        else:
            node_id, node_address = self.leader_id, self.leader_address

        print(f"{node_id} {node_address}")
        return GetLeaderResponse(nodeId=node_id, nodeAddress=node_address)

    def SetVal(self, request, context):
        # maybe log
        key, value = request.key, request.value
        return SetValResponse(success=None)

    def GetVal(self, request, context):
        key = request.key
        # maybe log
        return GetValResponse(success=None, value=None)

    def Suspend(self, request, context):
        pass


class SuspendableRaftElectionService(RaftElectionService):

    def __init__(self, server_id: int, server_address: str, servers: dict[int, str]) -> None:
        super().__init__(server_id, server_address, servers)
        self.suspended = False

    def RequestVote(self, request, context):
        return self.__wrap_with_suspend(super().RequestVote, request, context)

    def AppendEntries(self, request: AppendRequest, context):
        return self.__wrap_with_suspend(super().AppendEntries, request, context)

    def GetLeader(self, request, context):
        return self.__wrap_with_suspend(super().GetLeader, request, context)

    def SetVal(self, request, context):
        return self.__wrap_with_suspend(super().SetVal, request, context)

    def GetVal(self, request, context):
        return self.__wrap_with_suspend(super().GetVal, request, context)

    def Suspend(self, request, context):
        return self.__wrap_with_suspend(self.__suspend, request, context)

    # noinspection PyUnusedLocal
    def __suspend(self, request, context) -> Void:
        period = request.period
        print(f"Command from client: suspend {request.period}")

        was_follower = self.state == "follower"

        self.suspended = True

        # actual suspend only after function return
        start_after_time(period_sec=0.025, func=self.__make_suspend, period=period, was_follower=was_follower)

        return Void()

    def __make_suspend(self, period: int, was_follower: bool) -> None:
        self.state = "follower"
        self.election_timer.cancel()
        if self.leader_timer is not None:
            self.leader_timer.cancel()
        print(f"Sleeping for {period} seconds")
        time.sleep(period)

        # after wake up
        if was_follower:
            print(f"I am a follower. Term: {self.current_term}")
        self.election_timer = self.start_election_timer()

        self.suspended = False

    def __wrap_with_suspend(self, func: Callable, request, context) -> Void | Any:
        if self.suspended:
            msg = "Server is suspended"
            context.set_details(msg)
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            return Void()
        else:
            return func(request, context)


def configure_server(server_addr: str, server_id: int, other_servers_addrs: [str]):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    server.add_insecure_port(server_addr)
    print(f"The server starts at {server_addr}")
    service = SuspendableRaftElectionService(server_id, server_addr, other_servers_addrs)
    pb_grpc.add_RaftElectionServiceServicer_to_server(
        service,
        server
    )
    return service, server


def start_server() -> None:
    needed_server_id = int(sys.argv[1])
    config_file = open("config.conf", "r")
    servers = {}
    needed_server_address = None
    for server_line in config_file.read().splitlines():
        server_id, address = parse_server_config(server_line)
        if server_id == needed_server_id:
            needed_server_address = address
            continue
        servers[server_id] = address
    config_file.close()

    if needed_server_address is None:
        print("No such available server id")
        sys.exit()

    service, server = configure_server(server_addr=needed_server_address,
                                       server_id=needed_server_id,
                                       other_servers_addrs=servers)

    try:
        server.start()
        server.wait_for_termination()
    except KeyboardInterrupt:
        service.should_interrupt = True
        server.stop(grace=None)
        print("Shutting down")
        sys.exit(0)


if __name__ == "__main__":
    start_server()
