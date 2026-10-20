import { Settings2, Zap, Sparkles, Paintbrush, Smile, EyeOff, Gauge } from 'lucide-react';
import type { HealthStatus, SyntheticIdentity } from '../services/api';
import IdentitySelector from './IdentitySelector';

interface SettingsPanelProps {
  mode: 'image' | 'video';
  method: string;
  setMethod: (m: string) => void;
  identity: string;
  setIdentity: (id: string) => void;
  identities: SyntheticIdentity[];
  resolution: string;
  setResolution: (r: string) => void;
  uniquePerPerson: boolean;
  setUniquePerPerson: (v: boolean) => void;
  health: HealthStatus | null;
  onAnonymize: () => void;
  isProcessing: boolean;
  hasFile: boolean;
  loadingStateText?: string;
}

const SettingsPanel = ({
  mode,
  method,
  setMethod,
  identity,
  setIdentity,
  identities,
  resolution,
  setResolution,
  uniquePerPerson,
  setUniquePerPerson,
  health,
  onAnonymize,
  isProcessing,
  hasFile,
  loadingStateText
}: SettingsPanelProps) => {

  const styleOptions = [
    {
      id: 'generative',
      title: 'Realistic',
      icon: Sparkles,
      color: 'indigo',
      desc: 'Generative AI synthetic replacement (InSwapper 128)'
    },
    {
      id: 'cartoon',
      title: 'Cartoon',
      icon: Paintbrush,
      color: 'amber',
      desc: 'Bilateral color quantization & adaptive edge inking'
    },
    {
      id: 'anime',
      title: 'Anime',
      icon: Smile,
      color: 'pink',
      desc: 'Vibrant cel-shading & delicate Japanese anime contours'
    },
    {
      id: 'blur',
      title: 'Blur',
      icon: EyeOff,
      color: 'slate',
      desc: 'Traditional Gaussian privacy obscuration baseline'
    }
  ];

  return (
    <div className="glass-card p-6 h-full flex flex-col justify-between space-y-6">
      <div className="space-y-6">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <h3 className="text-lg font-bold flex items-center gap-2 text-slate-100">
            <Settings2 className="w-5 h-5 text-indigo-400" />
            Processing Configuration
          </h3>
          <span className="text-xs uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
            {mode} Mode
          </span>
        </div>

        {/* Style Selection Cards */}
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2.5">
            Anonymization Style
          </label>
          <div className="grid grid-cols-2 gap-2">
            {styleOptions.map((opt) => {
              const Icon = opt.icon;
              const isSelected = method === opt.id;
              return (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => setMethod(opt.id)}
                  className={`p-2.5 rounded-xl border text-left transition-all ${
                    isSelected
                      ? 'bg-indigo-600/20 border-indigo-500 ring-1 ring-indigo-500 shadow-sm'
                      : 'bg-slate-900/60 border-slate-800 hover:bg-slate-800/60 text-slate-400'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <Icon className={`w-4 h-4 ${isSelected ? 'text-indigo-400' : 'text-slate-400'}`} />
                    <span className={`text-xs font-bold ${isSelected ? 'text-white' : 'text-slate-300'}`}>
                      {opt.title}
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-400 line-clamp-1">{opt.desc}</p>
                </button>
              );
            })}
          </div>
        </div>

        {/* Video Resolution Settings (Only in video mode) */}
        {mode === 'video' && (
          <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
                <Gauge className="w-3.5 h-3.5 text-indigo-400" />
                Encoding Resolution
              </span>
              <span className="text-[10px] text-slate-500">Speed vs Quality</span>
            </div>
            <div className="grid grid-cols-3 gap-1.5 text-xs">
              {[
                { id: 'original', label: 'Original' },
                { id: '720p', label: '720p HD' },
                { id: '480p', label: '480p Fast' }
              ].map((res) => (
                <button
                  key={res.id}
                  type="button"
                  onClick={() => setResolution(res.id)}
                  className={`py-1.5 rounded-lg border font-semibold text-center transition-all ${
                    resolution === res.id
                      ? 'bg-indigo-600 text-white border-indigo-500'
                      : 'bg-slate-800/70 border-slate-700/60 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {res.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Synthetic Identity Selector (Shown when method is not blur) */}
        {method !== 'blur' && (
          <div className="animate-in fade-in slide-in-from-top-2 duration-300">
            <IdentitySelector
              identities={identities}
              selectedIdentity={identity}
              onSelectIdentity={setIdentity}
              uniquePerPerson={uniquePerPerson}
              onToggleUniquePerPerson={setUniquePerPerson}
            />
          </div>
        )}
      </div>

      {/* Action Button & Hardware Info */}
      <div className="pt-4 border-t border-slate-800 space-y-2.5">
        <div className="flex items-center justify-between text-[11px] text-slate-400">
          <span>Engine: <span className="font-semibold text-slate-200">{health?.inference || 'CPU'}</span></span>
          <span className="text-emerald-400 font-semibold">{health?.status === 'online' ? '● Ready' : '○ Initializing'}</span>
        </div>
        <button
          onClick={onAnonymize}
          disabled={!hasFile || isProcessing}
          className={`w-full py-3.5 px-6 rounded-xl font-bold flex items-center justify-center gap-2.5 transition-all text-sm ${
            hasFile && !isProcessing
              ? 'bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white shadow-[0_0_25px_rgba(99,102,241,0.35)] cursor-pointer'
              : 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
          }`}
        >
          {isProcessing ? (
            <div className="flex items-center gap-2.5">
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
              <span>{loadingStateText || "Processing..."}</span>
            </div>
          ) : (
            <>
              <Zap className="w-4 h-4 text-amber-300" />
              <span>{mode === 'image' ? 'ANONYMIZE IMAGE' : 'PROCESS VIDEO'}</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default SettingsPanel;
