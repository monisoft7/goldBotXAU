# Research Lab Timestamp And Session Policy

Version: v0_59

This policy documents timestamp and session assumptions for research use only. It does not shift timestamps, rewrite data, rerun strategy metrics, or reinterpret prior results.

## Current State

The v0_58 lab integrity audit found no explicit timezone column in the local CSV data. Because the broker timezone is not provably UTC from the checked-in evidence, v0_59 treats the timestamp basis as `unknown_or_broker_server_time`.

## Standard

- Future session-based research must state `timestamp_basis` explicitly.
- If broker time is not proven UTC, reports must use `timestamp_basis = unknown_or_broker_server_time`.
- Fixed session windows can be used for descriptive research, but reports must disclose the timestamp basis behind those windows.
- v0_59 performs no timestamp shifting.

## Machine Policy

- `timestamp_basis = unknown_or_broker_server_time`
- `broker_timezone_provably_utc = false`
- `future_session_research_must_state_timestamp_basis = true`
- `timestamp_shift_performed = false`
