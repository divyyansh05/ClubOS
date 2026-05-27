import React from "react";

interface ScoringWeights {
  severity: number;
  persistence: number;
  peer_gap: number;
  commercial: number;
  evidence: number;
}

export interface ScoreComponentBarProps {
  severity: number;
  persistence: number;
  peerGap: number;
  commercial: number;
  evidence: number;
  weights: ScoringWeights;
}

export function ScoreComponentBar({
  severity,
  persistence,
  peerGap,
  commercial,
  evidence,
  weights,
}: ScoreComponentBarProps) {
  const sevContrib = severity * weights.severity;
  const perContrib = persistence * weights.persistence;
  const gapContrib = peerGap * weights.peer_gap;
  const comContrib = commercial * weights.commercial;
  const evdContrib = evidence * weights.evidence;

  const totalContrib =
    sevContrib + perContrib + gapContrib + comContrib + evdContrib;

  // Handle edge case: all zeros
  if (totalContrib === 0) {
    return (
      <div className="w-full">
        <div className="h-2 flex overflow-hidden rounded-sm bg-stone-200 dark:bg-stone-800 w-full" />
        <div className="flex justify-between mt-2 font-mono">
          <div className="flex flex-col items-center">
            <span className="text-[9px] uppercase text-stone-500 dark:text-stone-400">SEV</span>
            <span className="text-[11px] text-stone-500 dark:text-stone-400">0.00</span>
          </div>
          <div className="flex flex-col items-center">
            <span className="text-[9px] uppercase text-stone-500 dark:text-stone-400">PER</span>
            <span className="text-[11px] text-stone-500 dark:text-stone-400">0.00</span>
          </div>
          <div className="flex flex-col items-center">
            <span className="text-[9px] uppercase text-stone-500 dark:text-stone-400">GAP</span>
            <span className="text-[11px] text-stone-500 dark:text-stone-400">0.00</span>
          </div>
          <div className="flex flex-col items-center">
            <span className="text-[9px] uppercase text-stone-500 dark:text-stone-400">COM</span>
            <span className="text-[11px] text-stone-500 dark:text-stone-400">0.00</span>
          </div>
          <div className="flex flex-col items-center">
            <span className="text-[9px] uppercase text-stone-500 dark:text-stone-400">EVD</span>
            <span className="text-[11px] text-stone-500 dark:text-stone-400">0.00</span>
          </div>
        </div>
      </div>
    );
  }

  const sevPct = (sevContrib / totalContrib) * 100;
  const perPct = (perContrib / totalContrib) * 100;
  const gapPct = (gapContrib / totalContrib) * 100;
  const comPct = (comContrib / totalContrib) * 100;
  const evdPct = (evdContrib / totalContrib) * 100;

  return (
    <div className="w-full">
      <div className="h-2 flex overflow-hidden rounded-sm">
        {sevPct > 0 && (
          <div
            className="bg-critical-light dark:bg-critical-dark transition-all hover:opacity-80 cursor-help"
            style={{ width: `${sevPct}%` }}
            title={`Severity: ${severity.toFixed(2)} / 1.00 → contributes ${sevContrib.toFixed(2)} of ${weights.severity.toFixed(2)}`}
          />
        )}
        {perPct > 0 && (
          <div
            className="bg-warning-light dark:bg-warning-dark transition-all hover:opacity-80 cursor-help"
            style={{ width: `${perPct}%` }}
            title={`Persistence: ${persistence.toFixed(2)} / 1.00 → contributes ${perContrib.toFixed(2)} of ${weights.persistence.toFixed(2)}`}
          />
        )}
        {gapPct > 0 && (
          <div
            className="bg-info-light dark:bg-info-dark transition-all hover:opacity-80 cursor-help"
            style={{ width: `${gapPct}%` }}
            title={`Peer Gap: ${peerGap.toFixed(2)} / 1.00 → contributes ${gapContrib.toFixed(2)} of ${weights.peer_gap.toFixed(2)}`}
          />
        )}
        {comPct > 0 && (
          <div
            className="bg-accent-light dark:bg-accent-dark transition-all hover:opacity-80 cursor-help"
            style={{ width: `${comPct}%` }}
            title={`Commercial: ${commercial.toFixed(2)} / 1.00 → contributes ${comContrib.toFixed(2)} of ${weights.commercial.toFixed(2)}`}
          />
        )}
        {evdPct > 0 && (
          <div
            className="bg-good-light dark:bg-good-dark transition-all hover:opacity-80 cursor-help"
            style={{ width: `${evdPct}%` }}
            title={`Evidence: ${evidence.toFixed(2)} / 1.00 → contributes ${evdContrib.toFixed(2)} of ${weights.evidence.toFixed(2)}`}
          />
        )}
      </div>

      <div className="flex justify-between mt-2 font-mono">
        <div className="flex flex-col items-center">
          <span className="text-[9px] uppercase text-stone-500 dark:text-stone-400">SEV</span>
          <span className="text-[11px] text-critical-light dark:text-critical-dark">{severity.toFixed(2)}</span>
        </div>
        <div className="flex flex-col items-center">
          <span className="text-[9px] uppercase text-stone-500 dark:text-stone-400">PER</span>
          <span className="text-[11px] text-warning-light dark:text-warning-dark">{persistence.toFixed(2)}</span>
        </div>
        <div className="flex flex-col items-center">
          <span className="text-[9px] uppercase text-stone-500 dark:text-stone-400">GAP</span>
          <span className="text-[11px] text-info-light dark:text-info-dark">{peerGap.toFixed(2)}</span>
        </div>
        <div className="flex flex-col items-center">
          <span className="text-[9px] uppercase text-stone-500 dark:text-stone-400">COM</span>
          <span className="text-[11px] text-accent-light dark:text-accent-dark">{commercial.toFixed(2)}</span>
        </div>
        <div className="flex flex-col items-center">
          <span className="text-[9px] uppercase text-stone-500 dark:text-stone-400">EVD</span>
          <span className="text-[11px] text-good-light dark:text-good-dark">{evidence.toFixed(2)}</span>
        </div>
      </div>
    </div>
  );
}
