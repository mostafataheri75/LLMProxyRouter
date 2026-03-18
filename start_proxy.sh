#!/usr/bin/env bash
set -Eeuo pipefail

###############################################################################
#                     LLM Proxy Router Launcher
#
# Starts run.py inside a tmux session so it persists after you disconnect.
#
# Usage:
#   ./start_proxy.sh                          # uses defaults below
#   ENV_MANAGER=uv ./start_proxy.sh           # use uv instead of conda
#
# To attach to the running tmux session:
#   tmux attach -t llm_proxy
#
# To stop the server:
#   tmux kill-session -t llm_proxy
#
###############################################################################

# =============================================================================
#  CONFIGURATION
# =============================================================================

HOST="0.0.0.0"
PORT="8000"

# -- Environment manager ------------------------------------------------------
ENV_MANAGER="${ENV_MANAGER:-conda}"
ENV_NAME="vllm"

# -- Tmux session name --------------------------------------------------------
TMUX_SESSION="${TMUX_SESSION:-llm_proxy}"

# -- Project directory --------------------------------------------------------
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

# =============================================================================
#  END OF CONFIGURATION
# =============================================================================

activate_env() {
  case "$ENV_MANAGER" in
    conda)
      if ! command -v conda >/dev/null 2>&1; then
        echo "ERROR: conda is not installed or not in PATH." >&2
        exit 1
      fi
      eval "$(conda shell.bash hook)"
      conda activate "$ENV_NAME"
      ;;
    uv)
      local venv_dir="$ENV_NAME"
      if [ ! -f "$venv_dir/bin/activate" ]; then
        venv_dir=".venv"
      fi
      if [ ! -f "$venv_dir/bin/activate" ]; then
        echo "ERROR: No virtualenv found. Create one first." >&2
        exit 1
      fi
      # shellcheck disable=SC1091
      source "$venv_dir/bin/activate"
      ;;
    *)
      echo "ERROR: Unknown ENV_MANAGER='$ENV_MANAGER'. Use 'conda' or 'uv'." >&2
      exit 1
      ;;
  esac
}

build_run_command() {
  local cmd="cd '${PROJECT_DIR}'; "

  case "$ENV_MANAGER" in
    conda)
      cmd+="eval \"\$(conda shell.bash hook)\"; conda activate '$ENV_NAME'; "
      ;;
    uv)
      local venv_dir="$ENV_NAME"
      if [ ! -f "$venv_dir/bin/activate" ]; then
        venv_dir=".venv"
      fi
      cmd+="source '$venv_dir/bin/activate'; "
      ;;
  esac

  cmd+="python run.py --host '${HOST}' --port '${PORT}'"
  echo "$cmd"
}

main() {
  echo "=============================================="
  echo "  LLM Proxy Router Launcher"
  echo "=============================================="
  echo "  Host:         $HOST"
  echo "  Port:         $PORT"
  echo "  Env manager:  $ENV_MANAGER"
  echo "  Tmux session: $TMUX_SESSION"
  echo "  Project dir:  $PROJECT_DIR"
  echo "=============================================="

  # Verify the environment works before launching tmux
  echo "[1/2] Verifying Python environment ($ENV_MANAGER: $ENV_NAME) ..."
  activate_env

  # Launch inside tmux
  echo "[2/2] Starting proxy in tmux session '$TMUX_SESSION' ..."
  tmux kill-session -t "$TMUX_SESSION" 2>/dev/null || true

  local run_cmd
  run_cmd="$(build_run_command)"

  tmux new-session -d -s "$TMUX_SESSION" bash -c "$run_cmd"

  echo ""
  echo "Proxy is starting in tmux session '$TMUX_SESSION'."
  echo ""
  echo "Useful commands:"
  echo "  tmux attach -t $TMUX_SESSION        # view logs"
  echo "  tmux kill-session -t $TMUX_SESSION   # stop the proxy"
  echo ""
  echo "API endpoint: http://${HOST}:${PORT}"
}

main "$@"
