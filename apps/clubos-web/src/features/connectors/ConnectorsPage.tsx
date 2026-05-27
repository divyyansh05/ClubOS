import { useEffect, useState } from "react";
import {
  fetchConnectorStatus,
  fetchConnectorData,
  type ConnectorStatus,
  type ConnectorDataResponse,
} from "../../lib/api";
import { abbreviateNumber } from "../../lib/formatNumber";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function ConnectorsPage() {
  const [statuses, setStatuses] = useState<ConnectorStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [youtubeData, setYoutubeData] = useState<ConnectorDataResponse | null>(null);
  const [wikipediaData, setWikipediaData] = useState<ConnectorDataResponse | null>(null);
  const [showArchitecture, setShowArchitecture] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const statusResp = await fetchConnectorStatus();
      setStatuses(statusResp.connectors);

      // Load data from connected connectors
      const youtubeConnected = statusResp.connectors.find(
        (c) => c.connector_id === "youtube" && c.status === "connected"
      );
      const wikiConnected = statusResp.connectors.find(
        (c) => c.connector_id === "wikipedia" && c.status === "connected"
      );

      if (youtubeConnected) {
        const ytData = await fetchConnectorData("youtube");
        setYoutubeData(ytData);
      }

      if (wikiConnected) {
        const wikiData = await fetchConnectorData("wikipedia", 30);
        setWikipediaData(wikiData);
      }
    } catch (error) {
      console.error("Failed to load connectors:", error);
    } finally {
      setLoading(false);
    }
  }

  function getStatusColor(status: string) {
    switch (status) {
      case "connected":
        return "bg-good-500 text-white";
      case "not_configured":
        return "bg-warning-500 text-white";
      case "error":
        return "bg-critical-500 text-white";
      default:
        return "bg-stone-400 text-white";
    }
  }

  function getAuthTypeBadge(authType: string) {
    const colors: Record<string, string> = {
      api_key: "bg-info-100 text-info-700 dark:bg-info-900 dark:text-info-200",
      oauth: "bg-accent-100 text-accent-700 dark:bg-accent-900 dark:text-accent-200",
      none: "bg-stone-200 text-stone-700 dark:bg-stone-700 dark:text-stone-200",
    };
    return colors[authType] || colors.none;
  }

  if (loading) {
    return (
      <div className="max-w-screen-xl mx-auto px-6 py-12">
        <div className="text-center text-stone-500">Loading connectors...</div>
      </div>
    );
  }

  return (
    <div className="max-w-screen-xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="font-headline text-3xl md:text-4xl mb-2">Live Data Connectors</h1>
          <p className="text-stone-600 dark:text-stone-400">
            Real-time data ingestion from external APIs
          </p>
        </div>
        <button
          onClick={loadData}
          className="px-4 py-2 bg-info-500 hover:bg-info-600 text-white rounded-md font-sans text-sm transition-colors"
        >
          Refresh Status
        </button>
      </div>

      {/* Section 1: Connector Status Cards */}
      <section className="mb-12">
        <h2 className="font-headline text-2xl mb-4">Connector Status</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {statuses.map((connector) => (
            <div
              key={connector.connector_id}
              className="bg-white dark:bg-stone-800 rounded-lg border border-stone-300 dark:border-stone-700 p-4"
            >
              <div className="flex items-start justify-between mb-3">
                <h3 className="font-sans font-semibold text-sm">{connector.name}</h3>
                <span
                  className={`${getStatusColor(connector.status)} text-xs px-2 py-1 rounded uppercase font-mono`}
                >
                  {connector.status === "connected" ? "✓ Connected" : connector.status === "not_configured" ? "Not Configured" : "Error"}
                </span>
              </div>

              <div className="space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-stone-600 dark:text-stone-400">Auth Type:</span>
                  <span className={`${getAuthTypeBadge(connector.auth_type)} px-2 py-0.5 rounded font-mono uppercase`}>
                    {connector.auth_type === "api_key" ? "API Key" : connector.auth_type === "oauth" ? "OAuth" : "No Auth"}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-stone-600 dark:text-stone-400">Data Type:</span>
                  <span className="text-stone-900 dark:text-stone-100 font-mono text-[10px]">
                    {connector.data_type}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-stone-600 dark:text-stone-400">Last Sync:</span>
                  <span className="text-stone-900 dark:text-stone-100 font-mono">
                    {connector.last_sync
                      ? new Date(connector.last_sync).toLocaleTimeString()
                      : "Never"}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-stone-600 dark:text-stone-400">Records:</span>
                  <span className="text-stone-900 dark:text-stone-100 font-mono font-bold">
                    {abbreviateNumber(connector.records_fetched)}
                  </span>
                </div>

                {connector.error_message && (
                  <div className="mt-2 pt-2 border-t border-stone-200 dark:border-stone-700">
                    <p className="text-critical-600 dark:text-critical-400 text-[10px] font-mono">
                      {connector.error_message}
                    </p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Section 2: Live Data from Connected Connectors */}
      {youtubeData && (
        <section className="mb-12">
          <h2 className="font-headline text-2xl mb-4">YouTube Channel Statistics</h2>
          <p className="text-xs text-stone-500 dark:text-stone-400 mb-4 font-mono">
            Live data from YouTube Data API v3 — fetched {new Date(youtubeData.fetched_at).toLocaleString()}
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            {youtubeData.records.slice(0, 3).map((record) => (
              <div
                key={record.metric}
                className="bg-white dark:bg-stone-800 rounded-lg border border-stone-300 dark:border-stone-700 p-6"
              >
                <div className="text-stone-600 dark:text-stone-400 text-sm mb-2">
                  {record.label}
                </div>
                <div className="font-headline text-3xl text-info-600 dark:text-info-400">
                  {abbreviateNumber(record.value)}
                </div>
              </div>
            ))}
          </div>

          {youtubeData.records.length > 3 && (
            <div className="bg-white dark:bg-stone-800 rounded-lg border border-stone-300 dark:border-stone-700 p-4">
              <h3 className="font-sans font-semibold mb-3">Latest 5 Videos</h3>
              <div className="space-y-2">
                {youtubeData.records.slice(3, 8).map((video, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between py-2 border-b border-stone-200 dark:border-stone-700 last:border-0"
                  >
                    <span className="text-sm text-stone-700 dark:text-stone-300 flex-1 truncate">
                      {video.label.replace("Views: ", "")}
                    </span>
                    <span className="font-mono font-bold text-info-600 dark:text-info-400 ml-4">
                      {abbreviateNumber(video.value)} views
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      )}

      {wikipediaData && wikipediaData.records.length > 0 && (
        <section className="mb-12">
          <h2 className="font-headline text-2xl mb-4">Wikipedia Pageviews — Last 30 Days</h2>
          <p className="text-xs text-stone-500 dark:text-stone-400 mb-4 font-mono">
            Brand attention proxy via Wikipedia Pageviews API — no auth required
          </p>

          <div className="bg-white dark:bg-stone-800 rounded-lg border border-stone-300 dark:border-stone-700 p-6">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart
                data={wikipediaData.records.map((r) => ({
                  date: r.date ? `${r.date.slice(6, 8)} ${new Date(r.date.slice(0, 4), parseInt(r.date.slice(4, 6)) - 1).toLocaleString('en', { month: 'short' })}` : "",
                  views: r.value,
                }))}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#E8E8E5" />
                <XAxis
                  dataKey="date"
                  stroke="#75756F"
                  style={{ fontSize: "11px" }}
                />
                <YAxis
                  stroke="#75756F"
                  style={{ fontSize: "11px" }}
                  tickFormatter={(val) => abbreviateNumber(val)}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#FAFAF8",
                    border: "1px solid #E8E8E5",
                    borderRadius: "4px",
                  }}
                  formatter={(value: number) => [abbreviateNumber(value), "Pageviews"]}
                />
                <Line
                  type="monotone"
                  dataKey="views"
                  stroke="#2563EB"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>
      )}

      {/* Section 3: Architecture Explanation */}
      <section className="mb-12">
        <div className="bg-stone-100 dark:bg-stone-800 rounded-lg border border-stone-300 dark:border-stone-700 p-6">
          <button
            onClick={() => setShowArchitecture(!showArchitecture)}
            className="w-full flex items-center justify-between text-left"
          >
            <h2 className="font-headline text-xl">How This Connects to ClubOS Production</h2>
            <span className="text-2xl">{showArchitecture ? "−" : "+"}</span>
          </button>

          {showArchitecture && (
            <div className="mt-4 text-sm text-stone-700 dark:text-stone-300 space-y-3 font-body">
              <p>
                These connectors demonstrate ClubOS's data ingestion architecture. In production,
                the same pattern connects to:
              </p>
              <ul className="list-disc list-inside space-y-1 ml-4">
                <li>
                  <strong>YouTube API (active)</strong> → streaming metrics, video performance
                </li>
                <li>
                  <strong>Google Analytics 4</strong> → website traffic, bounce rate, sessions
                </li>
                <li>
                  <strong>Adobe Analytics</strong> → advanced segmentation, campaign attribution
                </li>
                <li>
                  <strong>SimilarWeb</strong> → competitor website traffic benchmarking
                </li>
              </ul>
              <p className="pt-2">
                All connectors follow the same interface: <code className="bg-stone-200 dark:bg-stone-700 px-1 py-0.5 rounded font-mono text-xs">test_connection()</code>,{" "}
                <code className="bg-stone-200 dark:bg-stone-700 px-1 py-0.5 rounded font-mono text-xs">fetch()</code>,{" "}
                <code className="bg-stone-200 dark:bg-stone-700 px-1 py-0.5 rounded font-mono text-xs">to_metric_rows()</code>.
                Adding a new data source requires implementing three methods. Daily automated ingestion
                via Cloud Scheduler would trigger these connectors nightly, replacing manual CSV uploads
                with live data pipelines.
              </p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
