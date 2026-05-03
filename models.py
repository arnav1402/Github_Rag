# Data models for GitRAG application
from dataclasses import dataclass

@dataclass
class File:
    path: str
    content: str

@dataclass
class Chunk:
    id: str
    text: str
    source: str

@dataclass
class EmbeddingRequest:
    github_url: str

@dataclass
class AskRequest:
    github_url: str
    question: str

@dataclass
class ClearRequest:
    github_url: str

@dataclass
class QueryResult:
    id: str
    text: str
    source: str
    score: float
