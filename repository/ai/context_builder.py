from repository.indexing import chunker
from multiprocessing import context
from dataclasses import dataclass

from repository.models.code_chunk import CodeChunk


@dataclass(frozen=True)
class ContextItem:
    file_path: str
    chunk_type: str
    name: str | None
    start_line: int
    end_line: int
    content: str


class RepositoryContextBuilder:
    def _chunk_key(self, chunk: CodeChunk) -> tuple:
        return (
            chunk.file_path,
            chunk.start_line,
            chunk.end_line,
            chunk.chunk_type,
            chunk.name,
        )

    def build(
        self,
        chunks: list[CodeChunk],
        ) -> list[ContextItem]:

        if not chunks:
            return []

        seen = set()
        items = []

        for chunk in chunks:

            key = self._chunk_key(chunk)

            if key in seen:
                continue

            seen.add(key)

            items.append(
                ContextItem(
                file_path=chunk.file_path,
                chunk_type=chunk.chunk_type,
                name=chunk.name,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                content=chunk.content,
            )
        )

        return items

    def format(
        self,
        items: list[ContextItem],
        max_characters: int = 20_000,
    ) -> str:

        if not items:
            return ""

        sections = []
        total_characters = 0

        for item in items:

            header = (
                f"File: {item.file_path}\n"
                f"Type: {item.chunk_type}\n"
                f"Name: {item.name or 'anonymous'}\n"
                f"Lines: {item.start_line}-{item.end_line}"
            )

            section = (
                f"{header}\n"
                f"```python\n"
                f"{item.content}\n"
                f"```"
            )

            if (
                total_characters + len(section)
                > max_characters
            ):
                break

            sections.append(section)

            total_characters += len(section)

        return "\n\n".join(sections)
def test_format_context():

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

    items = builder.build(chunks)

    context = builder.format(items)

    assert "File: auth.py" in context
    assert "Type: function" in context
    assert "Name: login" in context
    assert "Lines: 1-2" in context
    assert "def login():" in context
def test_format_empty_context():

    builder = RepositoryContextBuilder()

    assert builder.format([]) == ""
def test_context_respects_character_budget():

    chunks = [
    CodeChunk(
        content="x" * 100,
        file_path="first.py",
        chunk_type="function",
        name="first",
        start_line=1,
        end_line=10,
    ),
    CodeChunk(
        content="y" * 100,
        file_path="second.py",
        chunk_type="function",
        name="second",
        start_line=20,
        end_line=30,
    ),
]

    builder = RepositoryContextBuilder()

    items = builder.build(chunks)

    context = builder.format(
        items,
        max_characters=250,
    )

    assert "first.py" in context
    assert "second.py" not in context