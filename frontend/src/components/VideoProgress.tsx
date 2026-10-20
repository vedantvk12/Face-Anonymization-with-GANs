import { Loader2, XCircle, Clock, Zap, Film } from 'lucide-react';
import type { VideoJobStatus } from '../services/api';

interface VideoProgressProps {
  status: VideoJobStatus;
  onCancel: () => void;
  isCancelling: boolean;
}

const VideoProgress = ({ status, onCancel, isCancelling }: VideoProgressProps) => {
  const isFinalizing = status.progress_percent >= 99 && status.status === 'processing';

  return (
    <div className="glass-card p-6 border-indigo-500/30 bg-indigo-950/20 space-y-5 animate-in fade-in duration-300">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-indigo-600/20 border border-indigo-500/30 text-indigo-400">
            <Film className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <span>{isFinalizing ? "Finalizing H.264 & Audio..." : "Processing Video..."}</span>
              <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-400" />
            </h4>
            <p className="text-xs text-slate-400">
              {status.filename} ({status.resolution})
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={onCancel}
          disabled={isCancelling}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-rose-500/30 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 text-xs font-semibold transition-all disabled:opacity-50"
        >
          <XCircle className="w-3.5 h-3.5" />
          {isCancelling ? "Cancelling..." : "Cancel Job"}
        </button>
      </div>

      {/* Progress Bar */}
      <div className="space-y-1.5">
        <div className="flex justify-between text-xs font-semibold text-slate-300">
          <span>{status.current_frame} / {status.total_frames} frames</span>
          <span className="text-indigo-400 font-bold">{status.progress_percent}%</span>
        </div>
        <div className="w-full h-2.5 bg-slate-900 rounded-full overflow-hidden border border-slate-800">
          <div 
            className="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-indigo-400 transition-all duration-300 rounded-full"
            style={{ width: `${Math.max(2, status.progress_percent)}%` }}
          ></div>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-3 pt-2 border-t border-slate-800/80 text-center">
        <div className="p-2.5 bg-slate-900/50 rounded-lg border border-slate-800">
          <p className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold mb-0.5 flex items-center justify-center gap-1">
            <Zap className="w-3 h-3 text-amber-400" /> Throughput
          </p>
          <p className="text-sm font-bold text-slate-200">{status.fps} FPS</p>
        </div>

        <div className="p-2.5 bg-slate-900/50 rounded-lg border border-slate-800">
          <p className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold mb-0.5 flex items-center justify-center gap-1">
            <Clock className="w-3 h-3 text-blue-400" /> Elapsed
          </p>
          <p className="text-sm font-bold text-slate-200">{status.elapsed_time}s</p>
        </div>

        <div className="p-2.5 bg-slate-900/50 rounded-lg border border-slate-800">
          <p className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold mb-0.5 flex items-center justify-center gap-1">
            <Clock className="w-3 h-3 text-emerald-400" /> Estimated Left
          </p>
          <p className="text-sm font-bold text-slate-200">
            {status.eta_seconds !== null ? `${status.eta_seconds}s` : "Calculating..."}
          </p>
        </div>
      </div>
    </div>
  );
};

export default VideoProgress;
