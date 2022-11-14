import multiprocessing
import random
import sys
import logging
import threading
from concurrent import futures

import grpc
import raft_pb2 as pb
import raft_pb2_grpc as pb_grpc

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

HEARTBEAT_INTERVAL = 50         # ms
ELECTION_INTERVAL = 3000, 4000  # ms


def parse_server_config(config: str) -> (int, str):
    params = config.split()
    return int(params[0]), f"{params[1]}:{params[2]}"


def generate_random_timeout() -> int:
    return random.randint(ELECTION_INTERVAL[0], ELECTION_INTERVAL[1])


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
        super().__init__()

    def start_election_timer(self) -> threading.Timer:
        """ Unit of timeout is ms """
        election_timer = threading.Timer(self.election_timeout / 1000, self.start_election)
        logger.info("Start election timer")
        election_timer.start()
        return election_timer

    def start_following(self):
        self.state = "follower"
        self.election_timer = self.start_election_timer()

    def start_election(self):
        logger.info("Election Timeout! The election has started")
        if self.state != "follower":
            return

        self.state = "candidate"
        self.current_term += 1
        self.current_vote = self.server_id
        number_of_voted = 1  # because server initially votes for itself

        queue = multiprocessing.Queue()

        for _, server_address in self.servers.items():
            if self.state != "candidate":
                logger.info("The server is no longer a candidate. The election is canceled")
                return
            self.request_election_vote(server_address, queue)

        while not queue.empty():
            vote_result = queue.get()
            if vote_result is None:  # if server is not responding
                continue

            if vote_result.term > self.current_term:
                logger.info("The candidate term is greater than the current. The server becomes follower")
                self.current_term = vote_result.term
                self.current_vote = None
                self.start_following()
                return
            if vote_result.result:
                number_of_voted += 1

        if number_of_voted > (len(self.servers) + 1) / 2:
            logger.info(f"({self.current_term}) The election is win. Current server becomes the leader")
            self.start_leading()
        else:
            logger.info("The election is lose. Current server generates new timeout and becomes the follower")
            self.election_timeout = generate_random_timeout()
            self.start_following()

    def request_election_vote(self, address: str, queue) -> None:
        channel = grpc.insecure_channel(address)
        client_stub = pb_grpc.RaftElectionServiceStub(channel)
        try:
            result = client_stub.RequestVote(
                pb.VoteRequest(candidateTerm=self.current_term, candidateId=self.server_id))
            logger.info(f"The server: {address} vote is: {result.term}, {result.result}")
            queue.put(result)
        except Exception as e:
            logger.info(f"The server: {address} is not responding:\n{e}")

    def start_leading(self):
        self.state = "leader"
        timer = RepeatTimer(HEARTBEAT_INTERVAL / 1000, function=self.send_heartbeat)
        timer.start()
        while self.state == "leader":
            pass
        timer.cancel()

    def send_heartbeat(self):
        logger.info("Send heartbeats to servers")
        for _, server_address in self.servers.items():
            channel = grpc.insecure_channel(server_address)
            client_stub = pb_grpc.RaftElectionServiceStub(channel)
            try:
                result = client_stub.AppendEntries(
                    pb.AppendRequest(leaderTerm=self.current_term, leaderId=self.server_id))
                logger.info(f"The server: {server_address} append response is: {result.term}, {result.success}")
                if not result.success:
                    self.current_term = result.term
                    self.state = "follower"
                    return
            except Exception as e:
                logger.info(f"The server: {server_address} is not responding:\n{e}")

    def RequestVote(self, request, context):
        # logger.info(f"({self.current_term}) RequestVote from: {request.candidateId}")
        if request.candidateTerm > self.current_term or \
                (request.candidateTerm == self.current_term and
                 (self.current_vote is None or self.current_vote == request.candidateId)):
            self.current_term = request.candidateTerm
            self.current_vote = request.candidateId
            if self.state != "follower":
                self.start_following()
            return pb.VoteResponse(term=self.current_term, result=True)
        else:
            return pb.VoteResponse(term=self.current_term, result=False)

    def AppendEntries(self, request: pb.AppendRequest, context):
        logger.info(
            f"({self.current_term}) AppendEntries: leaderId={request.leaderId}, leaderTerm={request.leaderTerm}")
        self.election_timer.cancel()
        self.election_timer = self.start_election_timer()

        if request.leaderTerm >= self.current_term:
            self.current_term = request.leaderTerm
            return pb.AppendResponse(term=self.current_term, success=True)
        else:
            return pb.AppendResponse(term=self.current_term, success=False)

    def GetLeader(self, request, context):
        logger.info(f"({self.current_term}) GetLeader")
        return super().GetLeader(request, context)

    def Suspend(self, request, context):
        logger.info(f"({self.current_term}) Suspend")
        return super().Suspend(request, context)


def start_server():
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

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    server.add_insecure_port(needed_server_address)
    pb_grpc.add_RaftElectionServiceServicer_to_server(
        RaftElectionService(needed_server_id, needed_server_address, servers), server)
    logger.info(f"Starts at {needed_server_address}")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    try:
        logging.basicConfig()
        start_server()
    except KeyboardInterrupt:
        logger.info("Shutting down")
        exit()
