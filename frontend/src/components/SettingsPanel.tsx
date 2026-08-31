import { Settings2, Zap } from 'lucide-react';
import type { HealthStatus } from '../services/api';

interface SettingsPanelProps {
  method: string;
  setMethod: (m: string) => void;
  identity: string;
  setIdentity: (id: string) => void;
  identities: string[];
  health: HealthStatus | null;
  onAnonymize: () => void;
  isProcessing: boolean;
  hasImage: boolean;
  loadingStateText?: string;
}

const SettingsPanel = ({ 
  method, setMethod, identity, setIdentity, identities, onAnonymize, isProcessing, hasImage, loadingStateText 
}: SettingsPanelProps) => {
  return (
    <div className="glass-card p-6 h-full flex flex-col">
      <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
        <Settings2 className="w-5 h-5 text-emerald-400" />
        Anonymization Settings
      </h3>

      <div className="space-y-6 flex-1">
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-3">Method</label>
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => setMethod('generative')}
              className={`p-3 rounded-lg border text-sm font-medium transition-all ${
                method === 'generative'
                  ? 'bg-indigo-600/20 border-indigo-500 text-indigo-300'
                  : 'bg-slate-800/50 border-slate-700 text-slate-400 hover:bg-slate-800'
              }`}
            >
              Generative
            </button>
            <button
              onClick={() => setMethod('blur')}
              className={`p-3 rounded-lg border text-sm font-medium transition-all ${
                method === 'blur'
                  ? 'bg-indigo-600/20 border-indigo-500 text-indigo-300'
                  : 'bg-slate-800/50 border-slate-700 text-slate-400 hover:bg-slate-800'
              }`}
            >
              Blur Baseline
            </button>
          </div>
        </div>

        {method === 'generative' && (
          <div className="animate-in fade-in slide-in-from-top-2 duration-300">
            <label className="block text-sm font-medium text-slate-300 mb-3">Synthetic Identity</label>
            <select
              value={identity}
              onChange={(e) => setIdentity(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg p-3 text-slate-200 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all"
            >
              <option value="random">Random</option>
              {identities.map(id => (
                <option key={id} value={id}>{id.replace(/_/g, ' ').toUpperCase()}</option>
              ))}
            </select>
          </div>
        )}

        <div className="p-4 bg-slate-800/30 border border-slate-700/50 rounded-lg">
          <p className="text-xs leading-relaxed text-slate-400">
            {method === 'generative' 
              ? "Generative anonymization replaces detected faces with synthetic identities while preserving facial pose and scene context."
              : "Blur anonymization obscures facial information and serves as a traditional baseline."}
          </p>
        </div>
      </div>

      <div className="mt-6">
        <button
          onClick={onAnonymize}
          disabled={!hasImage || isProcessing}
          className={`w-full py-4 px-6 rounded-xl font-bold flex items-center justify-center gap-2 transition-all ${
            hasImage && !isProcessing
              ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-[0_0_20px_rgba(79,70,229,0.3)]'
              : 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
          }`}
        >
          {isProcessing ? (
            <div className="flex items-center gap-3">
              <div className="w-5 h-5 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin"></div>
              <span>{loadingStateText || "Processing..."}</span>
            </div>
          ) : (
            <>
              <Zap className="w-5 h-5" />
              ANONYMIZE IMAGE
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default SettingsPanel;
