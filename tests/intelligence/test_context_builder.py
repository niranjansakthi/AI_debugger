from repository.intelligence.context_builder import (
    RepositoryContextBuilder,
)
from repository.models.code_chunk import CodeChunk


def test_build_context():

    chunks = [
        CodeChunk(
            content="def login():\n    pass",
            file_path="auth.py",
            chunk_type="function",
            name="login",
            start_line=1,
            end_line=2,
        )
    ]

    builder = RepositoryContextBuilder()

    context = builder.build(chunks)

    assert len(context) == 1

    item = context[0]

    assert item.file_path == "auth.py"
    assert item.chunk_type == "function"
    assert item.name == "login"
    assert item.start_line == 1
    assert item.end_line == 2
    assert item.content == "def login():\n    pass"

def test_empty_chunks():

    builder = RepositoryContextBuilder()

    assert builder.build([]) == []
