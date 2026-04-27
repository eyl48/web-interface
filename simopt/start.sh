echo "Starting SimOpt Web Interface..."
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$ROOT_DIR/.."
uvicorn simopt.server:app --reload --port 8000 &
BACKEND_PID=$!

echo ""
echo "SimOpt is running at http://localhost:8000"
echo "Press Ctrl+C to stop."

trap "echo 'Shutting down...'; kill $BACKEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM
wait