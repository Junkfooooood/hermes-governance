# Core memory pointers

- Hermes memory is layered.
- `SOUL.md` and `memory.md` only hold pointers.
- Plain text memory layer lives under `~/.hermes/memory/`; `~/.hermes/memories/` holds injected `MEMORY.md`/`USER.md` files.
- Keyword/tag retrieval lives in `fact_store/` and `skills/`.
- Semantic and timeline retrieval lives in `byterover/`.
- `mem0` handles durable extraction and write orchestration.
- `neo4j` holds relationship and timeline structure.
- `qdrant` handles vector recall.
- Important memories should be promoted gradually; obsolete ones should be archived.
- Skills should be merged when duplicated and retired when obsolete.
§
Hermes memory fixes on 2026-04-28: `memory_search` code path was valid; apparent empty results likely came from RediSearch indexing delay during same-session write/read. `memory.remove` AMS cleanup was fixed by bridging remove in `run_agent.py` and matching existing Redis memories by content substring in `init.py`. Additional fixes: `RedisBackend.scan_keys()`, safe `_search_working`, `search("*")` wildcard handling, and lifecycle promotion also runs after memory writes.
§
For complex multi-agent tasks in Hermes, the accepted governance architecture is 三省六部制: 中书省 planning, 门下省 review/veto/revision, 尚书省 dispatch with dependency-aware execution_order, 六部 level-by-level execution with same-level parallelism and inter-level sequencing, and 尚书省 integration. Use this architecture for high-complexity multi-agent coordination, not for simple tasks.
§
User's macOS OpenClaw install observed on 2026-04-29: OpenClaw 2026.4.26 at /opt/homebrew/bin/openclaw on Node v25.8.0, state ~/.openclaw, gateway localhost:18789, model minimax/MiniMax-M2.7. Issues found: LLM timeouts/stuck sessions from huge contexts and memory pressure; MiniMax/OpenAI image generation SSRF blocks caused by Shadowrocket TUN/Fake-IP DNS resolving domains to 198.18.0.x. Mitigation: launchd HTTP(S)_PROXY=http://127.0.0.1:1082 with local/private NO_PROXY and gateway restart; MiniMax image generation succeeded.