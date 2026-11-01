# Measurement

[README](../README.md) · [Docs](index.md)

The contract between a project's code and kanku's report. kanku doesn't
instrument anything: the project emits two kinds of line, and the report
reads them. *Why:* instrumentation is the project's code, in whatever
framework it uses; a log line is the narrowest seam every framework can
meet ([decisions/0005](decisions/0005-log-line-measurement.md)).

## The `llm_call` line

One line per model call, in the service's container log:

```text
llm_call model=<model id> duration=<seconds> status=<success|error> input_tokens=<n> output_tokens=<n> reasoning_tokens=<n> cached_tokens=<n>
```

- Anywhere in the line, after any prefix the logger adds — the report
  searches for `llm_call ` and reads the `key=value` pairs that follow.
- `duration` in seconds, decimal point, measured around the call.
- `input_tokens` includes `cached_tokens`; `reasoning_tokens` are part of
  `output_tokens` when the provider bills them so, and are reported apart
  so their share is visible.
- Missing counts are `0`, never omitted.

The report needs the container log captured with timestamps
(`docker compose logs --timestamps`), which the runner does. From these lines
it computes exact per-call latency (mean, p50, p90, p95, min, max) and the
effective cost:

```text
cost = (input_tokens − cached_tokens) × prompt
     + cached_tokens × cache_read            # prompt, when no cache price is published
     + output_tokens × completion
```

averaged per scenario over the repetitions.

## The test-start marker

The runner loads a pytest plugin that prints, at the start of each test:

```text
BENCHMARK_TEST_START <node id> <ISO 8601 UTC timestamp>
```

Each call is attributed to the test whose window — from its marker to the
next — contains the call's timestamp; calls outside every window are
reported as `unattributed`. This needs the scenarios to run sequentially.

## A service that doesn't emit the line

Its variables are decided from the catalog ([process step 7](process/benchmark.md#step-7--validate-empirically-unless-one-of-two-exceptions-holds)),
and the run report lists the service under *Pending*.

## Recipe: google-adk with LiteLLM

A subclass of `LiteLlm` that times `generate_content_async` and reads
ADK's usage metadata:

```python
import logging
import time

from google.adk.models.lite_llm import LiteLlm

logger = logging.getLogger(__name__)


class InstrumentedLiteLlm(LiteLlm):
    async def generate_content_async(self, llm_request, stream=False):
        started = time.perf_counter()
        status = "success"
        last_response = None
        try:
            async for response in super().generate_content_async(llm_request, stream):
                last_response = response
                yield response
        except Exception:
            status = "error"
            raise
        finally:
            usage = getattr(last_response, "usage_metadata", None)
            logger.info(
                "llm_call model=%s duration=%.3f status=%s input_tokens=%d "
                "output_tokens=%d reasoning_tokens=%d cached_tokens=%d",
                self.model,
                time.perf_counter() - started,
                status,
                getattr(usage, "prompt_token_count", 0) or 0,
                getattr(usage, "candidates_token_count", 0) or 0,
                getattr(usage, "thoughts_token_count", 0) or 0,
                getattr(usage, "cached_content_token_count", 0) or 0,
            )
```

Other frameworks: any wrapper that times the call and reads the provider's
usage block (OpenRouter returns `prompt_tokens`, `completion_tokens`,
`prompt_tokens_details.cached_tokens`,
`completion_tokens_details.reasoning_tokens`).
