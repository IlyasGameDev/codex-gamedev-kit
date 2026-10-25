#!/usr/bin/env bash
# Compatibility entry point retained for session-start.sh and old callers.
# Automatic update checks are disabled; this helper never uses the network.
_update_check_enabled() { return 1; }
update_check_notice() { return 0; }
update_check_refresh() {
  printf '%s\n' 'Automatic updates are disabled. Review UPGRADING.md before updating the kit.' >&2
  return 0
}
if [ "$0" = "$BASH_SOURCE" ]; then
  case "$1" in
    notice|"") update_check_notice ;;
    refresh) update_check_refresh ;;
    *) printf '%s\n' 'Usage: bash .codex/hooks/update-check.sh notice|refresh' >&2; exit 2 ;;
  esac
fi
