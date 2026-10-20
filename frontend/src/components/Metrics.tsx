import { Users, Clock, Zap, Hash, Copy, Check } from 'lucide-react';
import { useState } from 'react';

interface MetricsProps {
  facesDetected: number | null;
  processingTime: number | null;
  fps?: number | null;
  totalFrames?: number | null;
  hardware?: string | null;
  runId?: string | null;
}

const Metrics = ({
  facesDetected,
  processingTime,
  fps,
  totalFrames,
  hardware,
  runId
}: MetricsProps) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (runId) {
      navigator.clipboard.writeText(runId);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
      {/* Faces */}
      <div className="glass-card p-4 flex items-center gap-3">
        <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
          <Users className="w-5 h-5" />
        </div>
        <div>
          <p className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Faces Handled</p>
          <p className="text-xl font-black text-slate-100">
            {facesDetected !== null ? facesDetected : "-"}
          </p>
        </div>
      </div>

      {/* Latency / Frames */}
      <div className="glass-card p-4 flex items-center gap-3">
        <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
          <Clock className="w-5 h-5" />
        </div>
        <div>
          <p className="text-[10px] uppercase font-bold tracking-wider text-slate-400">
            {totalFrames ? 'Total Frames' : 'Processing Time'}
          </p>
          <p className="text-xl font-black text-slate-100">
            {totalFrames ? totalFrames : processingTime !== null ? `${processingTime}s` : "-"}
          </p>
        </div>
      </div>

      {/* Throughput */}
      <div className="glass-card p-4 flex items-center gap-3">
        <div className="p-2.5 rounded-xl bg-violet-500/10 border border-violet-500/20 text-violet-400">
          <Zap className="w-5 h-5" />
        </div>
        <div>
          <p className="text-[10px] uppercase font-bold tracking-wider text-slate-400">
            {fps ? 'Average Throughput' : 'Hardware Engine'}
          </p>
          <p className="text-xl font-black text-slate-100">
            {fps ? `${fps} FPS` : hardware || "GPU (DirectML)"}
          </p>
        </div>
      </div>

      {/* Run ID / Identifier */}
      <div className="glass-card p-4 flex items-center justify-between">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 shrink-0">
            <Hash className="w-5 h-5" />
          </div>
          <div className="overflow-hidden">
            <p className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Job Identifier</p>
            <p className="text-xs font-mono font-bold text-slate-200 truncate">
              {runId ? runId : "-"}
            </p>
          </div>
        </div>

        {runId && (
          <button
            onClick={handleCopy}
            title="Copy Run ID for Evaluation Lab"
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors shrink-0 ml-2"
          >
            {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
          </button>
        )}
      </div>
    </div>
  );
};

export default Metrics;
