---
name: openclaw-network-troubleshooting
description: "Use when OpenClaw or a similar local agent gateway fails provider/API/media calls due to DNS, proxy, VPN, fake-IP, SSRF, or private/internal/special-use IP errors. Diagnose resolver chain, proxy environment, provider code paths, and verify with minimal provider capability calls."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [openclaw, gateway, dns, proxy, ssrf, macos, troubleshooting]
    related_skills: [systematic-debugging, hermes-agent]
---

# OpenClaw Network Troubleshooting

## Overview

OpenClaw provider calls can fail even when the public API is reachable from `curl`. A common class of failures is interaction between OpenClaw's SSRF/private-network guard and local proxy/VPN DNS behavior, especially TUN/fake-IP clients on macOS. In that mode, public domains may resolve to special-use addresses such as `198.18.0.0/15`; OpenClaw correctly blocks those because provider requests set `allowPrivateNetwork: false`.

This skill focuses on finding the root cause without weakening OpenClaw's security model. Prefer fixing DNS/proxy routing or making OpenClaw use a trusted proxy path over disabling SSRF protection or allowing private networks globally.

## When to Use

Use this skill when:

- OpenClaw image/video/web/provider calls fail with errors like `resolves to private/internal/special-use IP address`.
- OpenClaw logs show `[security] blocked URL fetch` for public API domains.
- MiniMax, OpenAI, Google, Vertex, or other provider calls work in a browser or raw `curl` but fail inside OpenClaw.
- macOS is using Shadowrocket, Clash, Surge, Loon, sing-box, Tailscale, or any TUN/proxy/fake-IP DNS tool.
- You need to distinguish `/etc/hosts` pollution, DNS pollution, fake-IP DNS, proxy misconfiguration, and OpenClaw SSRF policy.

Do not use this skill for generic LLM timeouts without DNS/security errors; use `systematic-debugging` and inspect session/context size, provider latency, and model config first.

## Investigation Workflow

### 1. Read the exact OpenClaw error and logs

Check both gateway logs and error logs:

```bash
search_files(
  pattern="resolves to private|private/internal|special-use|blocked URL fetch|candidate failed|image-generation|video-generation",
  path="~/.openclaw/logs",
  target="content",
  context=2,
  limit=120,
)
```

or from shell:

```bash
grep -Ei 'resolves to private|special-use|blocked URL fetch|image-generation|video-generation' ~/.openclaw/logs/gateway*.log
```

Record the target origin from the log, e.g. `https://api.minimaxi.com`, `https://api.minimax.io`, `https://chatgpt.com`, or `https://vertexaisearch.cloud.google.com`.

### 2. Identify provider code paths and default domains

Search OpenClaw's installed package for the provider capability:

```bash
search_files(
  pattern="api\\.minimax|api\\.minimaxi|image_generation|video_generation|allowPrivateNetwork|resolveProviderHttpRequestConfig",
  path="/opt/homebrew/lib/node_modules/openclaw/dist",
  target="content",
  file_glob="*.js",
  context=3,
  limit=160,
)
```

For MiniMax in OpenClaw 2026.4.x:

- Image provider defaults to `https://api.minimax.io`, but switches to `https://api.minimaxi.com` when the configured/provider base URL is a `minimaxi.com` host.
- Image endpoint: `/v1/image_generation`.
- Video default base URL: `https://api.minimax.io` unless provider config overrides it.
- Video endpoints include `/v1/video_generation`, `/v1/query/video_generation`, and `/v1/files/retrieve`.
- Image/video providers pass `allowPrivateNetwork: false`; do not simply turn this off unless the user explicitly accepts the security tradeoff.

### 3. Compare system resolver vs public DNS

Run a compact resolver probe for suspected domains:

```bash
python3 - <<'PY'
import socket, subprocess
hosts=['api.minimax.io','api.minimaxi.com','chatgpt.com','vertexaisearch.cloud.google.com']
for h in hosts:
    print('\n##', h)
    try:
        infos=socket.getaddrinfo(h,443,type=socket.SOCK_STREAM)
        print('socket:', ', '.join(sorted({i[4][0] for i in infos})))
    except Exception as e:
        print('socket_error:', repr(e))
    for cmd in [['dig','+short',h], ['dig','@1.1.1.1','+short',h], ['dig','@223.5.5.5','+short',h]]:
        try:
            out=subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=8, text=True).strip()
            print(' '.join(cmd)+':', out.replace('\n', ', ') or '(empty)')
        except Exception as e:
            print(' '.join(cmd)+': ERR', repr(e))
PY
```

If `socket`/plain `dig` returns `198.18.0.x` while public DNS returns real public IPs, the likely cause is fake-IP DNS from a proxy/TUN client, not provider downtime.

### 4. Check macOS resolver, hosts, and proxy state

```bash
printf '%s\n' '--- hosts relevant lines ---'
grep -nEi 'minimax|minimaxi|openai|chatgpt|google|vertex|198\.18|127\.0|10\.|172\.|192\.168' /etc/hosts 2>/dev/null || true

printf '%s\n' '--- scutil dns ---'
scutil --dns | sed -n '1,220p'

printf '%s\n' '--- proxy env ---'
env | grep -Ei 'https?_proxy|all_proxy|no_proxy' || true

printf '%s\n' '--- macOS proxy settings ---'
scutil --proxy

printf '%s\n' '--- proxy/VPN/DNS processes ---'
ps axo pid,ppid,rss,comm,args | egrep -i 'shadowrocket|clash|mihomo|surge|loon|quantumult|stash|v2ray|sing-box|tailscale|proxy|dns' | egrep -v 'egrep|grep'

printf '%s\n' '--- local proxy listeners ---'
lsof -nP -iTCP:1082 -sTCP:LISTEN 2>/dev/null || true
lsof -nP -iTCP:7890 -sTCP:LISTEN 2>/dev/null || true
```

Interpretation:

- `/etc/hosts` has provider domains mapped to loopback/private/special-use IPs → hosts pollution; remove or correct those entries after user approval.
- `scutil --dns` nameserver is `198.18.0.2` and proxy app is active → likely TUN/fake-IP DNS.
- macOS proxy is set but OpenClaw's process lacks `HTTP_PROXY`/`HTTPS_PROXY` env vars → OpenClaw's strict SSRF guard may resolve fake-IP before the proxy handles the target.

## Safe Fix Patterns

### Preferred: configure proxy app DNS rules

If the proxy app supports it, add provider domains to fake-IP filter / real-IP DNS / DIRECT DNS handling, for example:

- `api.minimax.io`
- `api.minimaxi.com`
- `*.minimax.io`
- `*.minimaxi.com`
- Other domains shown in `[security] blocked URL fetch` logs

Then flush DNS and restart OpenClaw gateway. This keeps OpenClaw direct networking intact while avoiding fake-IP answers.

### Practical macOS mitigation: launchd HTTP(S) proxy env

If the local proxy exposes an HTTP proxy (example Shadowrocket `127.0.0.1:1082`), inject proxy variables into the user launchd environment and restart OpenClaw gateway:

```bash
launchctl setenv HTTP_PROXY http://127.0.0.1:1082
launchctl setenv HTTPS_PROXY http://127.0.0.1:1082
launchctl setenv http_proxy http://127.0.0.1:1082
launchctl setenv https_proxy http://127.0.0.1:1082
launchctl setenv NO_PROXY 'localhost,127.0.0.1,::1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,*.local'
launchctl setenv no_proxy 'localhost,127.0.0.1,::1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,*.local'
```

Then restart the gateway:

```bash
pid=$(lsof -nP -iTCP:18789 -sTCP:LISTEN -t 2>/dev/null | head -1 || true)
[ -n "$pid" ] && kill -TERM "$pid"
# Wait for service manager/launchd to bring it back, or start it manually if needed.
lsof -nP -iTCP:18789 -sTCP:LISTEN
```

Why this works: OpenClaw's guarded provider fetch has a trusted environment proxy mode. With `HTTP_PROXY`/`HTTPS_PROXY` set and no `NO_PROXY` match for the target, OpenClaw can use the proxy path instead of pinning a fake-IP DNS answer as the final destination.

Caution: this depends on the local proxy process staying up. If the user quits the proxy app, OpenClaw external API calls may fail until proxy env vars are unset or the proxy is restored.

### Avoid: allowing private network globally

Do not patch provider code to set `allowPrivateNetwork: true` for public providers unless the user explicitly asks and accepts SSRF risk. It masks fake-IP DNS symptoms by weakening an intentional security boundary.

## Verification

### Verify OpenClaw guarded request no longer hits SSRF block

From the OpenClaw dist directory, test the same guarded request helper. Use a harmless unauthenticated request; a provider business error such as missing Authorization means networking got past the DNS/SSRF guard.

```bash
cd /opt/homebrew/lib/node_modules/openclaw/dist
HTTPS_PROXY=http://127.0.0.1:1082 HTTP_PROXY=http://127.0.0.1:1082 \
NO_PROXY='localhost,127.0.0.1,::1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,*.local' \
node --input-type=module - <<'NODE'
import { a as postJsonRequest } from './shared-BaGWsvKy.js';
for (const host of ['api.minimax.io','api.minimaxi.com']) {
  try {
    const r = await postJsonRequest({
      url:`https://${host}/v1/image_generation`,
      headers:{'content-type':'application/json'},
      body:{model:'image-01', prompt:'test', n:1, response_format:'base64'},
      timeoutMs:15000,
      fetchFn:fetch,
      allowPrivateNetwork:false
    });
    console.log(host, 'status='+r.response.status, (await r.response.text()).slice(0,160));
    await r.release();
  } catch (e) {
    console.log(host, 'ERR', e && e.message || e);
  }
}
NODE
```

Good result: HTTP status/body from provider, even if auth fails. Bad result: `Blocked: resolves to private/internal/special-use IP address`.

### Verify a real capability call

If credentials are configured and cost is acceptable, run a minimal image generation:

```bash
HTTP_PROXY=http://127.0.0.1:1082 HTTPS_PROXY=http://127.0.0.1:1082 \
NO_PROXY='localhost,127.0.0.1,::1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,*.local' \
openclaw capability image generate \
  --model minimax/image-01 \
  --prompt 'simple blue circle on white background' \
  --aspect-ratio 1:1 \
  --count 1 \
  --timeout-ms 60000 \
  --output /tmp/openclaw-minimax-dns-test.png \
  --json

file /tmp/openclaw-minimax-dns-test.*
```

Then search for new SSRF blocks after the fix time:

```bash
grep -Ei 'api\.minimax|api\.minimaxi|private/internal|special-use' ~/.openclaw/logs/gateway.err.log | tail -40
```

## Rollback

Remove launchd proxy env vars if they cause unwanted behavior:

```bash
launchctl unsetenv HTTP_PROXY
launchctl unsetenv HTTPS_PROXY
launchctl unsetenv http_proxy
launchctl unsetenv https_proxy
launchctl unsetenv NO_PROXY
launchctl unsetenv no_proxy
```

Restart OpenClaw gateway afterwards.

## Common Pitfalls

1. **Assuming `curl` success proves OpenClaw should work.** `curl` may use system proxy behavior while OpenClaw's guarded fetch pins DNS before connecting.
2. **Confusing fake-IP with malicious DNS pollution.** `198.18.0.0/15` is often an intentional fake-IP pool used by proxy tools, but OpenClaw still must treat it as special-use.
3. **Putting provider domains in `NO_PROXY`.** That prevents trusted env proxy mode and can re-trigger strict fake-IP DNS pinning.
4. **Forgetting to restart the gateway.** Launchd environment changes only affect newly started processes.
5. **Reading only `gateway.log`.** Security blocks usually appear in `gateway.err.log`.
6. **Leaking API keys in reports.** Redact tokens, API keys, OAuth secrets, and connection strings. Business responses can be quoted only after removing credentials.

## Verification Checklist

- [ ] Exact blocked origin and error string captured from logs.
- [ ] `/etc/hosts` checked for provider-domain overrides.
- [ ] System resolver and public DNS compared for the blocked domain.
- [ ] Proxy/VPN/TUN process and local proxy port identified.
- [ ] Fix preserves `allowPrivateNetwork: false` for public provider calls.
- [ ] OpenClaw gateway restarted after env/DNS changes.
- [ ] Guarded request or real capability call succeeds without `private/internal/special-use` block.
- [ ] Recent logs show no new block for the tested provider domain.
