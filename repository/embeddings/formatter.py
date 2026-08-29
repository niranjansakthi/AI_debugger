from repository.models.code_chunk import CodeChunk


class CodeChunkFormatter:
    def format(self,chunk:CodeChunk) -> str:
        parts = [
            f"File: {chunk.file_path}",
            f"Type: {chunk.chunk_type},"
        ]
        if chunk.name:
            parts.append(f"Name: {chunk.name}")
        if chunk.parent_name:
            parts.append(f"Parent: {chunk.parent_name}")

        parts.append(
            f"Lines: {chunk.start_line}-{chunk.end_line}"
        )

        parts.append("")
        parts.append("Code:")
        parts.append(chunk.content)

        return "\n".join(parts)

   

    