# Owner deployment checklist

The local backend is installed as `~/.config/systemd/user/portfolio-ai-demo.service`. It listens only on 127.0.0.1:8021. The owner enabled Funnel on October 14, 2026. Public port 10000 is configured to proxy only this repair service. Existing Serve/RDP routes remain tailnet-only. The public relay passed live inference, session quota and single-use approval checks; both public DNS addresses now pass HTTPS hostname/chain validation with TLS 1.3. Edge currently reports a client-side address block; independent phone verification is still needed.

Deployment and verification checklist:

1. Sign in to the Tailscale administrator account and use the activation link printed by the CLI, or follow https://tailscale.com/docs/features/tailscale-funnel#enable-funnel . Review the default scope: activation ordinarily permits all tailnet members to use Funnel. Limit the policy to the intended device/user if necessary.
2. Confirm the local service is active: `systemctl --user is-active portfolio-ai-demo.service` . Check `http://127.0.0.1:8021/api/health` . It must report configured true without exposing any key.
3. Publish only the unused public port: `tailscale funnel --bg --https 10000 http://127.0.0.1:8021` . Do not reset existing Serve routes, use public ports 443/8443, or expose other dashboards.
4. Inspect `tailscale funnel status` . It should map only the intended public endpoint to localhost:8021. Existing routes must remain tailnet-only.
5. Verify https://ryzenator-ms7c56.tailf4551d.ts.net:10000/api/health from outside the tailnet; DNS propagation can take up to ten minutes. Visit the published portfolio and confirm live mode becomes available.
6. Test charging, missing-model, hazard, stock-unavailable and provider-failure behavior. Confirm the current server proposal alone can be approved, a second approval fails, quotas persist across restart and recorded mode remains available offline.
7. Measure public gateway latency/error behavior and update the report. Local API timings do not establish public latency or uptime.
8. Keep the machine powered on and connected. Monitor `/api/metrics` and the user service journal. This is a single-host demonstration with no uptime SLA.

To unpublish only this endpoint, use the installed CLI’s port-scoped off command (`tailscale funnel --https 10000 off`); verify status afterward. Do not use a global reset.

No live customer operations or financial orders are connected. The current service is a bounded synthetic demo, not a production repair system.
