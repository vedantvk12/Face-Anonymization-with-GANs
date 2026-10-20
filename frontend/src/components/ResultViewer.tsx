import { useState, useRef } from 'react';
import { Download, CheckCircle2 } from 'lucide-react';
import { getResultUrl } from '../services/api';

interface ResultViewerProps {
  type: 'image' | 'video';
  originalUrl: string;
  resultUrl: string;
  method: string;
  syntheticIdentity?: string | null;
  onReset?: () => void;
}

const ResultViewer = ({ type, originalUrl, resultUrl, method, syntheticIdentity, onReset }: ResultViewerProps) => {
  const [activeTab, setActiveTab] = useState<'comparison' | 'result' | 'original'>('comparison');
  const origVideoRef = useRef<HTMLVideoElement>(null);
  const resultVideoRef = useRef<HTMLVideoElement>(null);

  const handleDownload = async () => {
    try {
      const fullUrl = getResultUrl(resultUrl);
      const ext = type === 'video' ? 'mp4' : 'jpg';
      const response = await fetch(fullUrl);
      const blob = await response.blob();
      const blobUrl = URL.createObjectURL(blob);

      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = `anonymized_${method}_${Date.now()}.${ext}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      URL.revokeObjectURL(blobUrl);
    } catch (err) {
      console.error("Download failed:", err);
    }
  };

  // Sync play/pause between the two comparison video elements
  const handleOrigPlay = () => {
    if (resultVideoRef.current && resultVideoRef.current.paused) {
      resultVideoRef.current.play();
    }
  };

  const handleOrigPause = () => {
    if (resultVideoRef.current && !resultVideoRef.current.paused) {
      resultVideoRef.current.pause();
    }
  };

  const methodLabel = method.charAt(0).toUpperCase() + method.slice(1);

  return (
    <div className="glass-card p-6 h-full flex flex-col justify-between space-y-4 animate-in fade-in duration-500">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-100 flex items-center gap-2 flex-wrap">
              <span>{type === 'video' ? 'Anonymized Video' : 'Transformation Result'}</span>
              <span className="text-xs px-2 py-0.5 rounded-md bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 font-semibold">
                {methodLabel}
              </span>
              {syntheticIdentity && (
                <span className="text-xs px-2 py-0.5 rounded-md bg-emerald-600/20 text-emerald-300 border border-emerald-500/30 font-mono">
                  Identity: {syntheticIdentity}
                </span>
              )}
            </h3>
            <p className="text-xs text-slate-400">
              Identity altered while scene context & lighting are preserved
            </p>
          </div>
        </div>

        {/* Tab Controls */}
        <div className="flex bg-slate-900/80 rounded-lg p-1 border border-slate-800 text-xs">
          <button
            onClick={() => setActiveTab('original')}
            className={`px-3 py-1.5 rounded-md font-medium transition-all ${
              activeTab === 'original' ? 'bg-slate-800 text-white shadow' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Original
          </button>
          <button
            onClick={() => setActiveTab('result')}
            className={`px-3 py-1.5 rounded-md font-medium transition-all ${
              activeTab === 'result' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Anonymized
          </button>
          <button
            onClick={() => setActiveTab('comparison')}
            className={`px-3 py-1.5 rounded-md font-medium transition-all ${
              activeTab === 'comparison' ? 'bg-slate-800 text-white shadow' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Side-by-Side
          </button>
        </div>
      </div>

      {/* Main Display Area */}
      <div className="flex-1 min-h-[440px] relative rounded-xl overflow-hidden bg-slate-950 border border-slate-800 flex items-center justify-center p-3">
        {type === 'image' ? (
          <>
            {activeTab === 'original' && (
              <img
                src={getResultUrl(originalUrl)}
                alt="Original"
                className="max-w-full max-h-[420px] object-contain rounded-lg"
              />
            )}

            {activeTab === 'result' && (
              <img
                src={getResultUrl(resultUrl)}
                alt="Anonymized"
                className="max-w-full max-h-[420px] object-contain rounded-lg"
              />
            )}

            {activeTab === 'comparison' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full h-full items-center justify-center p-2">
                <div className="flex flex-col items-center">
                  <span className="text-[11px] text-slate-400 uppercase tracking-wider mb-2 font-bold">
                    Original Source
                  </span>
                  <img
                    src={getResultUrl(originalUrl)}
                    alt="Original"
                    className="max-w-full max-h-[350px] object-contain rounded-lg shadow-lg border border-slate-800"
                  />
                </div>
                <div className="flex flex-col items-center">
                  <span className="text-[11px] text-indigo-400 uppercase tracking-wider mb-2 font-bold">
                    Anonymized ({methodLabel})
                  </span>
                  <img
                    src={getResultUrl(resultUrl)}
                    alt="Anonymized"
                    className="max-w-full max-h-[350px] object-contain rounded-lg shadow-lg border border-indigo-900/60"
                  />
                </div>
              </div>
            )}
          </>
        ) : (
          /* Video Viewer */
          <>
            {activeTab === 'original' && (
              <video
                src={getResultUrl(originalUrl)}
                controls
                className="max-w-full max-h-[420px] rounded-lg"
              />
            )}

            {activeTab === 'result' && (
              <video
                src={getResultUrl(resultUrl)}
                controls
                autoPlay
                className="max-w-full max-h-[420px] rounded-lg"
              />
            )}

            {activeTab === 'comparison' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full h-full items-center justify-center p-2">
                <div className="flex flex-col items-center w-full">
                  <span className="text-[11px] text-slate-400 uppercase tracking-wider mb-2 font-bold">
                    Original Video
                  </span>
                  <video
                    ref={origVideoRef}
                    src={getResultUrl(originalUrl)}
                    controls
                    onPlay={handleOrigPlay}
                    onPause={handleOrigPause}
                    className="w-full max-h-[340px] rounded-lg border border-slate-800 bg-black"
                  />
                </div>
                <div className="flex flex-col items-center w-full">
                  <span className="text-[11px] text-indigo-400 uppercase tracking-wider mb-2 font-bold">
                    Anonymized ({methodLabel})
                  </span>
                  <video
                    ref={resultVideoRef}
                    src={getResultUrl(resultUrl)}
                    controls
                    className="w-full max-h-[340px] rounded-lg border border-indigo-900/60 bg-black"
                  />
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Footer Controls */}
      <div className="flex items-center justify-between pt-2">
        {onReset && (
          <button
            type="button"
            onClick={onReset}
            className="text-xs text-slate-400 hover:text-slate-200 transition-colors font-medium"
          >
            ← Upload Another {type === 'video' ? 'Video' : 'Image'}
          </button>
        )}

        <button
          onClick={handleDownload}
          className="btn-primary flex items-center gap-2 py-2 px-4 text-xs font-bold ml-auto"
        >
          <Download className="w-3.5 h-3.5" />
          Download {type === 'video' ? 'MP4 Video' : 'Image'}
        </button>
      </div>
    </div>
  );
};

export default ResultViewer;
