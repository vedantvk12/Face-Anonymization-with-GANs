import { useState } from 'react';
import { Activity, ShieldAlert, FileSearch, Film, Image as ImageIcon, Info } from 'lucide-react';
import { evaluateRun, evaluateVideoJob } from '../services/api';
import type { EvaluationResponse, VideoEvaluationResponse } from '../services/api';

const Evaluation = () => {
  const [evalType, setEvalType] = useState<'image' | 'video'>('image');
  const [targetId, setTargetId] = useState('');
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [imageResults, setImageResults] = useState<EvaluationResponse | null>(null);
  const [videoResults, setVideoResults] = useState<VideoEvaluationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleEvaluate = async () => {
    if (!targetId.trim()) return;
    setIsEvaluating(true);
    setError(null);

    try {
      if (evalType === 'image') {
        const data = await evaluateRun(targetId.trim());
        setImageResults(data);
        setVideoResults(null);
      } else {
        const data = await evaluateVideoJob(targetId.trim());
        setVideoResults(data);
        setImageResults(null);
      }
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || "Evaluation failed. Please verify that the ID exists and has completed processing.");
    } finally {
      setIsEvaluating(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      
      {/* Header and Input Form */}
      <div className="glass-card p-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
          <div>
            <h2 className="text-2xl font-bold flex items-center gap-3 text-slate-100">
              <FileSearch className="w-6 h-6 text-indigo-400" />
              Privacy & Utility Evaluation Lab
            </h2>
            <p className="text-slate-400 text-sm mt-1 max-w-2xl leading-relaxed">
              Measure empirical identity alteration and environmental scene preservation scores.
              Evaluation is on-demand to conserve GPU and CPU computing resources.
            </p>
          </div>

          {/* Type Selector */}
          <div className="flex bg-slate-900/90 p-1 rounded-xl border border-slate-800 text-xs self-start">
            <button
              type="button"
              onClick={() => { setEvalType('image'); setError(null); }}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold transition-all ${
                evalType === 'image' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <ImageIcon className="w-3.5 h-3.5" />
              Image Run
            </button>
            <button
              type="button"
              onClick={() => { setEvalType('video'); setError(null); }}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold transition-all ${
                evalType === 'video' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Film className="w-3.5 h-3.5" />
              Video Job
            </button>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 max-w-2xl mt-4">
          <input 
            type="text" 
            placeholder={evalType === 'image' ? "Enter Image Run ID..." : "Enter Video Job ID..."} 
            value={targetId}
            onChange={(e) => setTargetId(e.target.value)}
            className="flex-1 bg-slate-900/80 border border-slate-700/80 rounded-xl px-4 py-3 text-slate-200 text-sm font-mono focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
          />
          <button 
            onClick={handleEvaluate}
            disabled={!targetId.trim() || isEvaluating}
            className="btn-primary flex items-center justify-center min-w-[140px] text-sm font-bold"
          >
            {isEvaluating ? (
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
            ) : (
              "Run Evaluation"
            )}
          </button>
        </div>

        {error && (
          <div className="mt-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs inline-block">
            {error}
          </div>
        )}
      </div>

      {/* Image Evaluation Results */}
      {imageResults && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-in slide-in-from-bottom-4 duration-500">
          {/* Privacy Card */}
          <div className="glass-card p-6 flex flex-col justify-between space-y-6">
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-base font-bold flex items-center gap-2 text-rose-300">
                  <ShieldAlert className="w-5 h-5 text-rose-400" />
                  Identity Change Evaluation
                </h3>
                <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-rose-950/60 text-rose-400 border border-rose-800/60">
                  ArcFace Cosine Metric
                </span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed mb-6">
                Cosine similarity between deep ArcFace 512-d embeddings. Lower scores signify stronger identity divergence from original face.
              </p>

              <div className="space-y-4">
                <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                  <p className="text-[10px] uppercase tracking-wider text-slate-400 font-bold mb-1">
                    Original vs Anonymized
                  </p>
                  <p className="text-3xl font-black text-slate-100">
                    {imageResults.privacy.identity_similarity.generative !== null 
                      ? imageResults.privacy.identity_similarity.generative 
                      : "N/A"}
                  </p>
                  <p className="text-[11px] text-emerald-400 mt-1">
                    {imageResults.privacy.identity_similarity.generative !== null && imageResults.privacy.identity_similarity.generative < 0.35 
                      ? "✓ Significant identity alteration achieved" 
                      : "Identity alteration calculated"}
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                  <p className="text-[10px] uppercase tracking-wider text-slate-400 font-bold mb-1">
                    Original vs Blur Baseline
                  </p>
                  <p className="text-2xl font-bold text-slate-300">
                    {imageResults.privacy.identity_similarity.blur !== null 
                      ? imageResults.privacy.identity_similarity.blur 
                      : "N/A"}
                  </p>
                  <p className="text-[11px] text-slate-500 mt-1">Traditional obscuration benchmark</p>
                </div>
              </div>
            </div>

            <div className="p-3 bg-slate-900/40 rounded-lg border border-slate-800/80 text-[11px] text-slate-400 leading-relaxed">
              <span className="font-semibold text-slate-300">Note: </span>
              Low cosine similarity indicates substantial identity alteration under recognition models, but does not represent a mathematical guarantee of zero re-identification.
            </div>
          </div>

          {/* Utility Card */}
          <div className="glass-card p-6 flex flex-col justify-between space-y-6">
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-base font-bold flex items-center gap-2 text-indigo-300">
                  <Activity className="w-5 h-5 text-indigo-400" />
                  Scene Context & Utility Preservation
                </h3>
                <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-indigo-950/60 text-indigo-400 border border-indigo-800/60">
                  Background Integrity
                </span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed mb-6">
                Measures preservation of non-face environment, lighting, background, hair, and clothing without artifacts.
              </p>

              <div className="space-y-4">
                <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                  <p className="text-[10px] uppercase tracking-wider text-slate-400 font-bold mb-1">
                    Scene Preservation Score
                  </p>
                  <p className="text-3xl font-black text-indigo-400">
                    {imageResults.utility.scene_preservation.generative !== null 
                      ? `${imageResults.utility.scene_preservation.generative}%` 
                      : "N/A"}
                  </p>
                  <p className="text-[11px] text-slate-400 mt-1">
                    Non-face pixel difference: {imageResults.utility.non_face_difference?.generative ?? 0.0} / 255.0
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                  <p className="text-[10px] uppercase tracking-wider text-slate-400 font-bold mb-1">
                    Blur Baseline Preservation
                  </p>
                  <p className="text-2xl font-bold text-slate-300">
                    {imageResults.utility.scene_preservation.blur !== null 
                      ? `${imageResults.utility.scene_preservation.blur}%` 
                      : "N/A"}
                  </p>
                  <p className="text-[11px] text-slate-500 mt-1">Comparison with standard blur</p>
                </div>
              </div>
            </div>

            <div className="p-3 bg-slate-900/40 rounded-lg border border-slate-800/80 text-[11px] text-slate-400 leading-relaxed">
              <span className="font-semibold text-slate-300">Methodology: </span>
              Evaluated using masked L1 pixel-difference on non-facial regions to ensure background context is retained.
            </div>
          </div>
        </div>
      )}

      {/* Video Evaluation Results */}
      {videoResults && (
        <div className="space-y-6 animate-in slide-in-from-bottom-4 duration-500">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="glass-card p-6">
              <p className="text-xs uppercase tracking-wider font-bold text-slate-400 mb-1">
                Average Video Identity Similarity
              </p>
              <p className="text-4xl font-black text-rose-400">
                {videoResults.average_identity_similarity !== null 
                  ? videoResults.average_identity_similarity 
                  : "N/A"}
              </p>
              <p className="text-xs text-slate-400 mt-2">
                Across sampled keyframes. Lower indicates consistent temporal identity alteration.
              </p>
            </div>

            <div className="glass-card p-6">
              <p className="text-xs uppercase tracking-wider font-bold text-slate-400 mb-1">
                Average Video Scene Preservation
              </p>
              <p className="text-4xl font-black text-indigo-400">
                {videoResults.average_scene_preservation !== null 
                  ? `${videoResults.average_scene_preservation}%` 
                  : "N/A"}
              </p>
              <p className="text-xs text-slate-400 mt-2">
                {videoResults.sampling_method}
              </p>
            </div>
          </div>

          {/* Sampled Frames Breakdown */}
          <div className="glass-card p-6">
            <h4 className="text-sm font-bold text-slate-200 mb-4 flex items-center gap-2">
              <Activity className="w-4 h-4 text-indigo-400" />
              Sampled Keyframes Analysis
            </h4>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-900/80 text-slate-400 uppercase font-semibold border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-4">Frame Index</th>
                    <th className="py-2.5 px-4">Timestamp</th>
                    <th className="py-2.5 px-4">Identity Similarity</th>
                    <th className="py-2.5 px-4">Scene Preservation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {videoResults.samples.map((s, idx) => (
                    <tr key={idx} className="hover:bg-slate-900/40">
                      <td className="py-2.5 px-4 font-bold text-slate-200">Frame #{s.frame}</td>
                      <td className="py-2.5 px-4 text-slate-400">{s.timestamp_seconds}s</td>
                      <td className="py-2.5 px-4 text-rose-300 font-bold">
                        {s.identity_similarity !== null ? s.identity_similarity : "N/A"}
                      </td>
                      <td className="py-2.5 px-4 text-indigo-300 font-bold">
                        {s.scene_preservation !== null ? `${s.scene_preservation}%` : "N/A"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="mt-4 p-3 bg-slate-900/40 rounded-lg border border-slate-800/80 text-[11px] text-slate-400 leading-relaxed">
              <Info className="w-3.5 h-3.5 inline mr-1 text-slate-400" />
              {videoResults.interpretation}
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default Evaluation;
