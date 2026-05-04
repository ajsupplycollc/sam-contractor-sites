"""
Chunk coordinator for scaled SAM pipeline.
Splits targets into N chunks, writes chunk files for parallel subagent processing.
Each chunk is self-contained: targets + sheet row offset + output directory.

Usage:
  python process_chunks.py [targets_json] [num_chunks]
  python process_chunks.py scaled_targets.json 5

Each chunk file (chunk_1.json ... chunk_N.json) contains:
  - targets: list of target dicts
  - sheet_start_row: first row in Google Sheet for this chunk
  - chunk_id: 1-based chunk number

After chunking, the orchestrator (Claude Code main session) spawns N subagents,
each running: python process_single_chunk.py chunk_N.json
"""
import json, os, sys, math

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = r'C:\Users\ajsup\sam_contractor_sites'
SHEET_ID = '1Fdfh-s3fF32l5FwxqGm3jeKS9_6B0NF07lx1q5TFrLM'
GOG = r'C:\Users\ajsup\gogcli\gog.exe'


def get_current_sheet_row_count() -> int:
    import subprocess
    result = subprocess.run(
        [GOG, 'sheets', 'get', SHEET_ID, 'Sheet1!A:A'],
        capture_output=True, text=True, encoding='utf-8'
    )
    lines = [l for l in result.stdout.strip().split('\n') if l.strip()]
    return len(lines)


def split_targets(targets: list, num_chunks: int, sheet_start_row: int) -> list[dict]:
    chunk_size = math.ceil(len(targets) / num_chunks)
    chunks = []
    for i in range(num_chunks):
        start = i * chunk_size
        end = min(start + chunk_size, len(targets))
        if start >= len(targets):
            break
        chunk = {
            "chunk_id": i + 1,
            "targets": targets[start:end],
            "sheet_start_row": sheet_start_row + start,
            "sheet_id": SHEET_ID,
            "base_dir": BASE_DIR,
        }
        chunks.append(chunk)
    return chunks


def main():
    targets_file = sys.argv[1] if len(sys.argv) > 1 else 'scaled_targets.json'
    num_chunks = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    targets_path = os.path.join(BASE_DIR, targets_file)
    with open(targets_path, 'r', encoding='utf-8') as f:
        targets = json.load(f)

    print(f"Loaded {len(targets)} targets from {targets_file}")
    print(f"Splitting into {num_chunks} chunks")

    current_rows = get_current_sheet_row_count()
    sheet_start_row = current_rows + 1
    print(f"Sheet currently has {current_rows} rows, new data starts at row {sheet_start_row}")

    chunks = split_targets(targets, num_chunks, sheet_start_row)

    for chunk in chunks:
        chunk_file = os.path.join(BASE_DIR, f"chunk_{chunk['chunk_id']}.json")
        with open(chunk_file, 'w', encoding='utf-8') as f:
            json.dump(chunk, f, indent=2, ensure_ascii=False)
        print(f"  chunk_{chunk['chunk_id']}.json: {len(chunk['targets'])} targets, sheet rows {chunk['sheet_start_row']}-{chunk['sheet_start_row'] + len(chunk['targets']) - 1}")

    print(f"\nChunks ready. Spawn {len(chunks)} subagents, each running:")
    print(f"  python process_single_chunk.py chunk_N.json")

    summary = {
        "total_targets": len(targets),
        "num_chunks": len(chunks),
        "sheet_start_row": sheet_start_row,
        "chunks": [{"id": c["chunk_id"], "count": len(c["targets"]), "file": f"chunk_{c['chunk_id']}.json"} for c in chunks]
    }
    summary_path = os.path.join(BASE_DIR, 'chunk_summary.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    print(f"\nSummary saved to: {summary_path}")


if __name__ == '__main__':
    main()
