import { ArrowDown, Camera, ScanFace, ImagePlus, Fingerprint, ShieldCheck } from 'lucide-react';

const Architecture = () => {
  return (
    <div className="py-8">
      <div className="flex flex-col items-center max-w-2xl mx-auto relative">
        
        {/* Step 1 */}
        <div className="w-full glass-card p-6 flex items-center gap-4 relative z-10 border-indigo-500/30">
          <div className="w-12 h-12 rounded-xl bg-slate-800 flex items-center justify-center shrink-0 border border-slate-700">
            <Camera className="w-6 h-6 text-slate-300" />
          </div>
          <div>
            <h4 className="font-bold text-slate-200">Input Image</h4>
            <p className="text-xs text-slate-400 mt-1">User uploads an image containing one or more faces.</p>
          </div>
        </div>
        
        <ArrowDown className="w-6 h-6 text-slate-600 my-3" />
        
        {/* Step 2 */}
        <div className="w-full glass-card p-6 flex items-center gap-4 relative z-10">
          <div className="w-12 h-12 rounded-xl bg-slate-800 flex items-center justify-center shrink-0 border border-slate-700">
            <ScanFace className="w-6 h-6 text-indigo-400" />
          </div>
          <div>
            <h4 className="font-bold text-slate-200">InsightFace Detection</h4>
            <p className="text-xs text-slate-400 mt-1">Extracts face regions and generates embeddings.</p>
          </div>
        </div>
        
        <ArrowDown className="w-6 h-6 text-slate-600 my-3" />

        {/* Step 3 */}
        <div className="w-full glass-card p-6 flex items-center gap-4 relative z-10 border-emerald-500/30">
          <div className="w-12 h-12 rounded-xl bg-emerald-900/30 flex items-center justify-center shrink-0 border border-emerald-500/50">
            <ImagePlus className="w-6 h-6 text-emerald-400" />
          </div>
          <div>
            <h4 className="font-bold text-slate-200">Generative Face Replacement</h4>
            <p className="text-xs text-slate-400 mt-1">InSwapper model maps synthetic identity onto the face region.</p>
          </div>
        </div>
        
        <ArrowDown className="w-6 h-6 text-slate-600 my-3" />

        {/* Step 4 */}
        <div className="w-full glass-card p-6 flex items-center gap-4 relative z-10">
          <div className="w-12 h-12 rounded-xl bg-slate-800 flex items-center justify-center shrink-0 border border-slate-700">
            <Fingerprint className="w-6 h-6 text-sky-400" />
          </div>
          <div>
            <h4 className="font-bold text-slate-200">Anonymized Output</h4>
            <p className="text-xs text-slate-400 mt-1">Final image compiled with modified faces and preserved scene.</p>
          </div>
        </div>
        
        <ArrowDown className="w-6 h-6 text-slate-600 my-3" />

        {/* Step 5 */}
        <div className="w-full glass-card p-6 flex items-center gap-4 relative z-10">
          <div className="w-12 h-12 rounded-xl bg-slate-800 flex items-center justify-center shrink-0 border border-slate-700">
            <ShieldCheck className="w-6 h-6 text-rose-400" />
          </div>
          <div>
            <h4 className="font-bold text-slate-200">Privacy & Utility Evaluation</h4>
            <p className="text-xs text-slate-400 mt-1">Optional metrics computation (Cosine similarity, pixel differences).</p>
          </div>
        </div>

      </div>
    </div>
  );
};

export default Architecture;
