import re

TIMESTAMP = re.compile(
    r"(?P<start>\d{1,2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*"
    r"(?P<end>\d{1,2}:\d{2}:\d{2}[,.]\d{3})"
)


def _seconds(value: str) -> float:
    hours, minutes, tail = value.replace(",", ".").split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(tail)


def parse_transcript(content: str, filename: str) -> list[dict[str, object]]:
    text = content.replace("\r\n", "\n").strip()
    if not text:
        raise ValueError("Transkrip kosong")
    if filename.lower().endswith(".txt"):
        return [{"start_seconds": 0.0, "end_seconds": None, "text": text}]

    segments: list[dict[str, object]] = []
    for block in re.split(r"\n\s*\n", text):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        timing_index: int | None = next(
            (index for index, line in enumerate(lines) if TIMESTAMP.search(line)),
            None,
        )
        if timing_index is None:
            continue
        match = TIMESTAMP.search(lines[timing_index])
        caption = " ".join(lines[timing_index + 1 :]).strip()
        if match and caption:
            segments.append(
                {
                    "start_seconds": _seconds(match.group("start")),
                    "end_seconds": _seconds(match.group("end")),
                    "text": re.sub(r"<[^>]+>", "", caption),
                }
            )
    if not segments:
        raise ValueError("Timestamp SRT/VTT tidak ditemukan")
    return segments


def group_topic_candidates(
    segments: list[dict[str, object]],
    max_gap_seconds: float = 30,
    max_duration_seconds: float = 300,
) -> list[dict[str, object]]:
    groups: list[list[dict[str, object]]] = []
    for segment in segments:
        if not groups:
            groups.append([segment])
            continue
        current = groups[-1]
        group_start = float(current[0]["start_seconds"])
        previous_end = current[-1]["end_seconds"]
        segment_start = float(segment["start_seconds"])
        gap = segment_start - float(previous_end or segment_start)
        if gap > max_gap_seconds or segment_start - group_start > max_duration_seconds:
            groups.append([segment])
        else:
            current.append(segment)

    return [
        {
            "candidate_number": index,
            "start_seconds": group[0]["start_seconds"],
            "end_seconds": group[-1]["end_seconds"],
            "title": str(group[0]["text"]).split(".")[0][:120],
            "text": " ".join(str(segment["text"]) for segment in group),
        }
        for index, group in enumerate(groups, start=1)
    ]
