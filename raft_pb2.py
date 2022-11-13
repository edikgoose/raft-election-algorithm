# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: raft.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\nraft.proto\"9\n\x0bVoteRequest\x12\x15\n\rcandidateTerm\x18\x01 \x01(\x04\x12\x13\n\x0b\x63\x61ndidateId\x18\x02 \x01(\x04\",\n\x0cVoteResponse\x12\x0c\n\x04term\x18\x01 \x01(\x04\x12\x0e\n\x06result\x18\x02 \x01(\x08\"5\n\rAppendRequest\x12\x12\n\nleaderTerm\x18\x01 \x01(\x04\x12\x10\n\x08leaderId\x18\x02 \x01(\x04\"/\n\x0e\x41ppendResponse\x12\x0c\n\x04term\x18\x01 \x01(\x04\x12\x0f\n\x07success\x18\x02 \x01(\x08\"\x06\n\x04Void\"8\n\x11GetLeaderResponse\x12\x0e\n\x06nodeId\x18\x01 \x01(\x04\x12\x13\n\x0bnodeAddress\x18\x02 \x01(\t\" \n\x0eSuspendRequest\x12\x0e\n\x06period\x18\x01 \x01(\x04\x32\xbe\x01\n\x13RaftElectionService\x12*\n\x0bRequestVote\x12\x0c.VoteRequest\x1a\r.VoteResponse\x12\x30\n\rAppendEntries\x12\x0e.AppendRequest\x1a\x0f.AppendResponse\x12&\n\tGetLeader\x12\x05.Void\x1a\x12.GetLeaderResponse\x12!\n\x07Suspend\x12\x0f.SuspendRequest\x1a\x05.Voidb\x06proto3')



_VOTEREQUEST = DESCRIPTOR.message_types_by_name['VoteRequest']
_VOTERESPONSE = DESCRIPTOR.message_types_by_name['VoteResponse']
_APPENDREQUEST = DESCRIPTOR.message_types_by_name['AppendRequest']
_APPENDRESPONSE = DESCRIPTOR.message_types_by_name['AppendResponse']
_VOID = DESCRIPTOR.message_types_by_name['Void']
_GETLEADERRESPONSE = DESCRIPTOR.message_types_by_name['GetLeaderResponse']
_SUSPENDREQUEST = DESCRIPTOR.message_types_by_name['SuspendRequest']
VoteRequest = _reflection.GeneratedProtocolMessageType('VoteRequest', (_message.Message,), {
  'DESCRIPTOR' : _VOTEREQUEST,
  '__module__' : 'raft_pb2'
  # @@protoc_insertion_point(class_scope:VoteRequest)
  })
_sym_db.RegisterMessage(VoteRequest)

VoteResponse = _reflection.GeneratedProtocolMessageType('VoteResponse', (_message.Message,), {
  'DESCRIPTOR' : _VOTERESPONSE,
  '__module__' : 'raft_pb2'
  # @@protoc_insertion_point(class_scope:VoteResponse)
  })
_sym_db.RegisterMessage(VoteResponse)

AppendRequest = _reflection.GeneratedProtocolMessageType('AppendRequest', (_message.Message,), {
  'DESCRIPTOR' : _APPENDREQUEST,
  '__module__' : 'raft_pb2'
  # @@protoc_insertion_point(class_scope:AppendRequest)
  })
_sym_db.RegisterMessage(AppendRequest)

AppendResponse = _reflection.GeneratedProtocolMessageType('AppendResponse', (_message.Message,), {
  'DESCRIPTOR' : _APPENDRESPONSE,
  '__module__' : 'raft_pb2'
  # @@protoc_insertion_point(class_scope:AppendResponse)
  })
_sym_db.RegisterMessage(AppendResponse)

Void = _reflection.GeneratedProtocolMessageType('Void', (_message.Message,), {
  'DESCRIPTOR' : _VOID,
  '__module__' : 'raft_pb2'
  # @@protoc_insertion_point(class_scope:Void)
  })
_sym_db.RegisterMessage(Void)

GetLeaderResponse = _reflection.GeneratedProtocolMessageType('GetLeaderResponse', (_message.Message,), {
  'DESCRIPTOR' : _GETLEADERRESPONSE,
  '__module__' : 'raft_pb2'
  # @@protoc_insertion_point(class_scope:GetLeaderResponse)
  })
_sym_db.RegisterMessage(GetLeaderResponse)

SuspendRequest = _reflection.GeneratedProtocolMessageType('SuspendRequest', (_message.Message,), {
  'DESCRIPTOR' : _SUSPENDREQUEST,
  '__module__' : 'raft_pb2'
  # @@protoc_insertion_point(class_scope:SuspendRequest)
  })
_sym_db.RegisterMessage(SuspendRequest)

_RAFTELECTIONSERVICE = DESCRIPTOR.services_by_name['RaftElectionService']
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _VOTEREQUEST._serialized_start=14
  _VOTEREQUEST._serialized_end=71
  _VOTERESPONSE._serialized_start=73
  _VOTERESPONSE._serialized_end=117
  _APPENDREQUEST._serialized_start=119
  _APPENDREQUEST._serialized_end=172
  _APPENDRESPONSE._serialized_start=174
  _APPENDRESPONSE._serialized_end=221
  _VOID._serialized_start=223
  _VOID._serialized_end=229
  _GETLEADERRESPONSE._serialized_start=231
  _GETLEADERRESPONSE._serialized_end=287
  _SUSPENDREQUEST._serialized_start=289
  _SUSPENDREQUEST._serialized_end=321
  _RAFTELECTIONSERVICE._serialized_start=324
  _RAFTELECTIONSERVICE._serialized_end=514
# @@protoc_insertion_point(module_scope)
