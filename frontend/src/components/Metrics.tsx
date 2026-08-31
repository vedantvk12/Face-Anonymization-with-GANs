import { Activity } from 'lucide-react';

interface MetricsProps {
  facesDetected: number | null;
  processingTime: number | null;
}

const Metrics = ({ facesDetected, processingTime }: MetricsProps) => {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
      <div className="glass-panel p-5">
        <p className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold mb-1">Faces Detected</p>
        <p className="text-2xl font-black text-white">{facesDetected !== null ? facesDetected : '—'}</p>
      </div>
      
      <div className="glass-panel p-5">
        <p className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold mb-1">Processing Time</p>
        <p className="text-2xl font-black text-white">{processingTime !== null ? `${processingTime}s` : '—'}</p>
      </div>
      
      <div className="glass-panel p-5 opacity-60">
        <p className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold mb-1 flex items-center gap-1">
          Identity Similarity <Activity className="w-3 h-3" />
        </p>
        <p className="text-lg font-bold text-slate-300 mt-1">Not evaluated</p>
      </div>
      
      <div className="glass-panel p-5 opacity-60">
        <p className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold mb-1 flex items-center gap-1">
          Scene Preservation <Activity className="w-3 h-3" />
        </p>
        <p className="text-lg font-bold text-slate-300 mt-1">Not evaluated</p>
      </div>
    </div>
  );
};

export default Metrics;
