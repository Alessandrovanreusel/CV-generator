#!/bin/bash
# Ralph Loop - CV Generator autonomous build loop
# Usage: ./ralph.sh [max_iterations]
set -e

echo "Starting Ralph Loop..."
MAX_ITERATIONS=${1:-15}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRD_FILE="$SCRIPT_DIR/prd.json"
PROGRESS_FILE="$SCRIPT_DIR/progress.txt"

if [ ! -f "$PROGRESS_FILE" ]; then
  echo "# CV Generator - Ralph Progress Log" > "$PROGRESS_FILE"
  echo "Started: $(date)" >> "$PROGRESS_FILE"
  echo "---" >> "$PROGRESS_FILE"
fi

echo "============================================="
echo "  CV Generator - Ralph Loop"
echo "  Max iterations: $MAX_ITERATIONS"
echo "============================================="

for i in $(seq 1 $MAX_ITERATIONS); do
  echo ""
  echo "======================================================="
  echo "  Iteration $i of $MAX_ITERATIONS — $(date)"
  echo "======================================================="

  PRD_FILE_WIN=$(cygpath -w "$PRD_FILE" 2>/dev/null || echo "$PRD_FILE")
  REMAINING=$(python -c "
import json, os
prd_path = r'$PRD_FILE_WIN'
with open(prd_path) as f:
    prd = json.load(f)
remaining = [s['id'] for s in prd['userStories'] if not s['passes']]
print(len(remaining))
if remaining:
    print(f'Next: {remaining[0]}')
" 2>&1) || true

  if echo "$REMAINING" | head -1 | grep -q "^0$"; then
    echo "All stories complete!"
    exit 0
  fi

  echo "$REMAINING"

  OUTPUT=$(claude --dangerously-skip-permissions --print \
    "Read CLAUDE.md for your instructions. Then read prd.json, progress.txt, and AGENTS.md. Implement the next incomplete story." \
    2>&1) || true
  echo "$OUTPUT"

  if echo "$OUTPUT" | grep -q "RALPH_COMPLETE"; then
    echo ""
    echo "Ralph completed all tasks at iteration $i!"
    exit 0
  fi

  echo "Iteration $i complete. Sleeping 5s..."
  sleep 5
done

echo "Ralph reached max iterations ($MAX_ITERATIONS)."
exit 1
