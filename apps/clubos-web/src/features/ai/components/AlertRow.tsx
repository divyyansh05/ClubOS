import { Link } from 'react-router-dom';
import { SeverityBadge } from './SeverityBadge';
import type { WatchdogAlertRead } from '../api/types';

const ALERT_TYPE_LABELS: Record<string, string> = {
  new_in_top_n: 'New in Top N',
  rank_jumped_into_top: 'Rank Jump ↑',
  rank_dropped_significantly: 'Rank Drop ↓',
  score_jump: 'Score Jump',
  dropped_out_of_top_n: 'Dropped Out',
  persistent_top: 'Persistent Top',
};

function formatDateShort(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

interface AlertRowProps {
  alert: WatchdogAlertRead;
  onAcknowledge: (alertId: string) => void;
  acknowledging: boolean;
}

export function AlertRow({ alert, onAcknowledge, acknowledging }: AlertRowProps) {
  const rankDelta = alert.rank_delta != null
    ? (alert.rank_delta > 0 ? `+${alert.rank_delta}` : `${alert.rank_delta}`)
    : '—';

  const scoreDelta = alert.score_previous != null
    ? (alert.score_current - alert.score_previous).toFixed(2)
    : null;

  return (
    <tr className="border-b border-stone-200 dark:border-stone-700 hover:bg-stone-50 dark:hover:bg-stone-800/50 transition-colors">
      <td className="px-3 py-3">
        <SeverityBadge severity={alert.severity} />
      </td>
      <td className="px-3 py-3">
        <Link
          to={`/ai/alerts/${alert.alert_id}`}
          className="font-mono text-sm text-ink dark:text-stone-100 hover:text-info-light dark:hover:text-info-dark transition-colors"
        >
          {alert.metric_name}
        </Link>
        {alert.acknowledged_at && (
          <span className="ml-2 font-mono text-[10px] uppercase tracking-wider text-stone-400 dark:text-stone-500">
            acked
          </span>
        )}
      </td>
      <td className="px-3 py-3 font-mono text-xs text-stone-600 dark:text-stone-300">
        {ALERT_TYPE_LABELS[alert.alert_type] ?? alert.alert_type}
      </td>
      <td className="px-3 py-3 font-mono text-sm text-center">
        <span className="text-stone-500 dark:text-stone-400">
          #{alert.current_rank}
        </span>
        {alert.previous_rank != null && (
          <span className={`ml-1.5 text-xs ${alert.rank_delta != null && alert.rank_delta > 0 ? 'text-critical-light dark:text-critical-dark' : 'text-good-light dark:text-good-dark'}`}>
            ({rankDelta})
          </span>
        )}
      </td>
      <td className="px-3 py-3 font-mono text-sm text-center">
        <span>{alert.score_current.toFixed(2)}</span>
        {scoreDelta != null && (
          <span className={`ml-1.5 text-xs ${parseFloat(scoreDelta) > 0 ? 'text-critical-light dark:text-critical-dark' : 'text-good-light dark:text-good-dark'}`}>
            ({parseFloat(scoreDelta) > 0 ? '+' : ''}{scoreDelta})
          </span>
        )}
      </td>
      <td className="px-3 py-3 font-mono text-xs text-stone-500 dark:text-stone-400">
        {formatDateShort(alert.created_at)}
      </td>
      <td className="px-3 py-3 text-right">
        {!alert.acknowledged_at && (
          <button
            onClick={() => onAcknowledge(alert.alert_id)}
            disabled={acknowledging}
            className="font-mono text-[10px] uppercase tracking-wider px-2 py-1 border border-stone-300 dark:border-stone-600 hover:border-ink dark:hover:border-stone-400 text-stone-500 dark:text-stone-400 hover:text-ink dark:hover:text-stone-100 transition-colors disabled:opacity-40"
          >
            Ack
          </button>
        )}
      </td>
    </tr>
  );
}
