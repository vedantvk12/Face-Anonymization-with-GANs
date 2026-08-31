import { useState } from 'react';
import { Activity, ShieldAlert, FileSearch } from 'lucide-react';
import { evaluateRun } from '../services/api';
import type { EvaluationResponse } from '../services/api';

const Evaluation = () => {
  const [runId, setRunId] = useState('');
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [results, setResults] = useState<EvaluationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleEvaluate = async () => {
    if (!runId) return;
    setIsEvaluating(true);
    setError(null);
    try {
      const data = await evaluateRun(runId);
      setResults(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to evaluate the run ID.");
    } finally {
      setIsEvaluating(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      
      <div className="glass-card p-8">
        <h2 className="text-2xl font-bold mb-2 flex items-center gap-3">
          <FileSearch className="w-6 h-6 text-indigo-400" />
          Run Evaluation
        </h2>
        <p className="text-slate-400 mb-6 max-w-2xl text-sm leading-relaxed">
          Enter the Run ID of a processed image to calculate experimental privacy and utility indicators. 
          Evaluation is not run automatically to conserve CPU resources.
        </p>

        <div className="flex flex-col md:flex-row gap-4 max-w-xl">
          <input 
            type="text" 
            placeholder="Enter Run ID..." 
            value={runId}
            onChange={(e) => setRunId(e.target.value)}
            className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-slate-200 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
          />
          <button 
            onClick={handleEvaluate}
            disabled={!runId || isEvaluating}
            className="btn-primary flex items-center justify-center min-w-[140px]"
          >
            {isEvaluating ? (
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
            ) : (
              "Evaluate"
            )}
          </button>
        </div>

        {error && (
          <div className="mt-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm inline-block">
            {error}
          </div>
        )}
      </div>

      {results && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-in slide-in-from-bottom-4 duration-500">
          {/* Privacy */}
          <div className="glass-card p-8">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-bold flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-rose-400" />
                Privacy Evaluation
              </h3>
            </div>
            
            <p className="text-xs text-slate-400 mb-6">
              Identity similarity is used as an experimental identity leakage indicator. Lower similarity suggests greater identity alteration.
            </p>

            <div className="space-y-6">
              <div>
                <p className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold mb-2">Original vs Generative (Cosine Similarity)</p>
                <p className="text-3xl font-black text-slate-200">
                  {results.privacy.identity_similarity.generative !== null ? results.privacy.identity_similarity.generative : "N/A"}
                </p>
              </div>
              
              <div className="w-full h-px bg-slate-800"></div>
              
              <div>
                <p className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold mb-2">Original vs Blur (Cosine Similarity)</p>
                <p className="text-3xl font-black text-slate-200">
                  {results.privacy.identity_similarity.blur !== null ? results.privacy.identity_similarity.blur : "N/A"}
                </p>
              </div>
            </div>
          </div>

          {/* Utility */}
          <div className="glass-card p-8">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-bold flex items-center gap-2">
                <Activity className="w-5 h-5 text-emerald-400" />
                Scene Utility
              </h3>
            </div>
            
            <p className="text-xs text-slate-400 mb-6">
              Lower non-face change indicates stronger preservation of the surrounding scene context.
            </p>

            <div className="space-y-6">
              <div>
                <p className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold mb-2">Generative Scene Preservation Score</p>
                <p className="text-3xl font-black text-slate-200">
                  {results.utility.scene_preservation.generative !== null ? `${results.utility.scene_preservation.generative}/100` : "N/A"}
                </p>
              </div>
              
              <div className="w-full h-px bg-slate-800"></div>
              
              <div>
                <p className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold mb-2">Blur Scene Preservation Score</p>
                <p className="text-3xl font-black text-slate-200">
                  {results.utility.scene_preservation.blur !== null ? `${results.utility.scene_preservation.blur}/100` : "N/A"}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Evaluation;
