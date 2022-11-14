# def start_election_timer(self, timeout: int) -> threading.Timer:
#     """ Unit of timeout is ms """
#     election_timer = threading.Timer(timeout / 1000, self.start_election_thread)
#     logger.info("Start election timer")
#     election_timer.start()
#     return election_timer
# def start_election_thread(self) -> None:
#     thread = threading.Thread(target=self.start_election)
#     thread.start()
#
#
# def start_election(self) -> None:
#     logger.info("Election Timeout. Start election")
#     self.state = "candidate"
#     self.current_vote = self.server_id
#     number_of_voted = 1  # 1 because server initially votes for itself
#
#     vote_
#     for _, address in self.servers.items():
#         thread = threading.Thread(target=self.request_election_vote, args=address)
#         thread.start()
#         thread.join()
#
#     for vote_result in vote_results:
#         if vote_result is None:  # if server is not responding
#             continue
#
#         if vote_result.term > self.current_term:
#             self.current_term = vote_result.term
#             self.start_following()
#             self.current_vote = None
#             return
#         if vote_result.result:
#             number_of_voted += 1
#     if number_of_voted > (len(self.servers) + 1) / 2:
#         logger.info("The election is win. Current server becomes the leader")
#         self.start_leading()
#     else:
#         logger.info("The election is lose. Current server generates new timeout and becomes the follower")
#     self.election_timeout = generate_random_timeout()
#     self.start_following()
#
#
# def request_election_vote(self, address: str) -> None:
#     channel = grpc.insecure_channel(address)
#     client_stub = pb_grpc.RaftElectionServiceStub(channel)
#     try:
#         result = client_stub.RequestVote(
#             pb.VoteRequest(candidateTerm=self.current_term, candidateId=self.server_id))
#         print(f"Request vote result: {result.term}, {result.result}")
#     except Exception as ex:
#         logger.info(f"The server: {address} is not responding.")
#
#
# def start_leading(self):
#     logger.info("LEADING")
#     pass


import concurrent
import multiprocessing
import random
import sys
import threading
import logging
from concurrent import futures

import grpc
import raft_pb2 as pb
import raft_pb2_grpc as pb_grpc

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def parse_server_config(config: str) -> tuple[int, str]:
    params = config.split()
    return int(params[0]), f"{params[1]}:{params[2]}"


def generate_random_timeout() -> int:
    return random.randint(1000, 2000)


class RaftElectionService(pb_grpc.RaftElectionServiceServicer):

    def RequestVote(self, request, context):
        logger.info(f"Request vote from: {request.candidateId}")
        return pb.VoteResponse(term=1, result=True)

    def AppendEntries(self, request: pb.AppendRequest, context):
        logger.info(f"Received: leaderId={request.leaderId}, leaderTerm={request.leaderTerm}")
        return pb.AppendResponse(term=1, success=True)

    def GetLeader(self, request, context):
        return super().GetLeader(request, context)

    def Suspend(self, request, context):
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
    pb_grpc.add_RaftElectionServiceServicer_to_server(RaftElectionService(), server)
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
