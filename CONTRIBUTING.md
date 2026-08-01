# Contributing

## Adding a collector

1. Create `src/linux_opt/<area>/collector.py` with a class extending
   `linux_opt.core.base.Collector`, decorated with `@register_collector`.
2. Implement `collect()` returning a plain dict. Don't catch exceptions
   yourself -- `Collector.run()` already wraps `collect()` and turns any
   exception into a `FAILED` result.
3. Read system state through `linux_opt.utils.procfs`'s helpers
   (`read_text`, `read_lines`, `read_kv_file`, `list_dir`), not raw
   `open()` calls, so missing files and permission errors are handled
   consistently with every other collector.
4. Add one import line to `_load_collectors()` in `src/linux_opt/cli/main.py`.
   That's the only CLI change a new collector needs -- the registry and
   `linux-opt scan`/`analyze` pick it up automatically.

## Adding an analyzer

Same shape as a collector: extend `linux_opt.core.base.Analyzer`, decorate
with `@register_analyzer`, implement `analyze(results)` returning a list of
`Recommendation`. `results` is the full dict of every collector's output
keyed by name -- an analyzer can read more than one collector's data (see
`SchedulerAnalyzer`, which reads both `scheduler` and `cpu`).

## Adding a plugin

Extend `linux_opt.plugins.base.Plugin`, decorate with `@register_plugin`,
implement `detect()` (cheap, side-effect-free presence check), `collect()`,
and `analyze()`. Add an import line to `_load_plugins()` in `cli/main.py`.
See `plugins/postgres.py` for a minimal example.

## Testing

```bash
pip install -e ".[dev]"
pytest tests/unit
```

Prefer testing against `tmp_path`-backed plain files over mocking
`/proc`/`/sys` directly -- see `tests/unit/test_procfs.py` for the pattern.
This keeps tests running the same way on any OS, since the procfs helpers
just read arbitrary paths.

## Code style

- No comments explaining *what* code does -- only *why*, when it's
  non-obvious (a workaround, a subtle invariant, a spec citation that
  matters for a future reader).
- Prefer extending an existing collector/analyzer/plugin pattern over
  inventing a new one; check `core/base.py` and an existing implementation
  before adding a new abstraction.
