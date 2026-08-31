import { useState } from 'react';
import { Download, LayoutTemplate } from 'lucide-react';
import { getResultUrl } from '../services/api';

interface ResultViewerProps {
  originalUrl: string;
  resultUrl: string;
  method: string;
}

const ResultViewer = ({ originalUrl, resultUrl, method }: ResultViewerProps) => {
  const [activeTab, setActiveTab] = useState<'comparison' | 'original' | 'result'>('comparison');
  
  const handleDownload = async () => {
    try {
      const response = await fetch(getResultUrl(resultUrl));
      const blob = await response.blob();
      const blobUrl = URL.createObjectURL(blob);
      
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = `anonymized_${method}_${Date.now()}.jpg`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      URL.revokeObjectURL(blobUrl);
    } catch (err) {
      console.error("Download failed:", err);
    }
  };

  return (
    <div className="glass-card p-6 h-full flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold flex items-center gap-2">
          <LayoutTemplate className="w-5 h-5 text-indigo-400" />
          Transformation Result
        </h3>
        
        <div className="flex bg-slate-800/50 rounded-lg p-1 border border-slate-700/50">
          <button
            onClick={() => setActiveTab('original')}
            className={`px-4 py-1.5 rounded-md text-xs font-medium transition-all ${
              activeTab === 'original' ? 'bg-slate-700 text-white shadow' : 'text-slate-400 hover:text-slate-300'
            }`}
          >
            Original
          </button>
          <button
            onClick={() => setActiveTab('result')}
            className={`px-4 py-1.5 rounded-md text-xs font-medium transition-all ${
              activeTab === 'result' ? 'bg-slate-700 text-white shadow' : 'text-slate-400 hover:text-slate-300'
            }`}
          >
            {method === 'generative' ? 'Generative' : 'Blur'}
          </button>
          <button
            onClick={() => setActiveTab('comparison')}
            className={`px-4 py-1.5 rounded-md text-xs font-medium transition-all ${
              activeTab === 'comparison' ? 'bg-slate-700 text-white shadow' : 'text-slate-400 hover:text-slate-300'
            }`}
          >
            Comparison
          </button>
        </div>
      </div>

      <div className="flex-1 min-h-[400px] relative rounded-xl overflow-hidden bg-slate-950 border border-slate-800 flex items-center justify-center p-4">
        {activeTab === 'original' && (
          <img src={getResultUrl(originalUrl)} alt="Original" className="max-w-full max-h-full object-contain rounded-lg" />
        )}
        
        {activeTab === 'result' && (
          <img src={getResultUrl(resultUrl)} alt="Anonymized" className="max-w-full max-h-full object-contain rounded-lg" />
        )}
        
        {activeTab === 'comparison' && (
          <div className="flex flex-col md:flex-row gap-4 w-full h-full items-center justify-center">
            <div className="flex-1 flex flex-col items-center">
              <span className="text-xs text-slate-400 uppercase tracking-wider mb-2 font-semibold">Original</span>
              <img src={getResultUrl(originalUrl)} alt="Original" className="max-w-full max-h-[300px] object-contain rounded-lg shadow-lg border border-slate-800" />
            </div>
            <div className="hidden md:block w-px h-1/2 bg-slate-800"></div>
            <div className="flex-1 flex flex-col items-center">
              <span className="text-xs text-indigo-400 uppercase tracking-wider mb-2 font-semibold">Anonymized</span>
              <img src={getResultUrl(resultUrl)} alt="Anonymized" className="max-w-full max-h-[300px] object-contain rounded-lg shadow-lg border border-indigo-900/50" />
            </div>
          </div>
        )}
      </div>

      <div className="mt-6 flex justify-end">
        <button onClick={handleDownload} className="btn-secondary flex items-center gap-2 py-2.5">
          <Download className="w-4 h-4" />
          Download Anonymized Image
        </button>
      </div>
    </div>
  );
};

export default ResultViewer;
