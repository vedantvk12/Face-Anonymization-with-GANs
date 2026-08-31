import Architecture from '../components/Architecture';

const About = () => {
  return (
    <div className="max-w-4xl mx-auto py-8 space-y-12 animate-in fade-in duration-500">
      
      <section>
        <h1 className="text-3xl font-black text-white mb-4">About PRIVAI</h1>
        <p className="text-slate-300 leading-relaxed text-lg max-w-2xl">
          PRIVAI is an Enterprise AI Privacy Platform focusing on privacy-preserving face anonymization. 
          It utilizes AI-based synthetic face replacement to protect identities in images while preserving 
          the context and utility of the scene.
        </p>
      </section>

      <section className="glass-card p-8">
        <h2 className="text-2xl font-bold mb-6 text-slate-100">Technical Details</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-4 bg-slate-800/40 rounded-xl border border-slate-700/50">
            <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold mb-1">Face Detection</p>
            <p className="font-medium text-slate-200">InsightFace (buffalo_l)</p>
          </div>
          
          <div className="p-4 bg-slate-800/40 rounded-xl border border-slate-700/50">
            <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold mb-1">Generative Replacement</p>
            <p className="font-medium text-slate-200">InSwapper 128</p>
          </div>
          
          <div className="p-4 bg-slate-800/40 rounded-xl border border-slate-700/50">
            <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold mb-1">Image Processing</p>
            <p className="font-medium text-slate-200">OpenCV</p>
          </div>
          
          <div className="p-4 bg-slate-800/40 rounded-xl border border-slate-700/50">
            <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold mb-1">Inference</p>
            <p className="font-medium text-slate-200">ONNX Runtime / CPU Execution</p>
          </div>
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-bold mb-6 text-slate-100">System Architecture</h2>
        <Architecture />
      </section>

      <section className="glass-card p-8 border-rose-500/20 bg-rose-950/10">
        <h2 className="text-xl font-bold mb-4 text-rose-400">Privacy & Limitations</h2>
        <ul className="space-y-3 text-sm text-rose-200/80 list-disc pl-5">
          <li>Generative anonymization reduces identity information but does not mathematically guarantee anonymity.</li>
          <li>Face recognition models may still extract residual identity information in highly constrained environments.</li>
          <li>Performance is highly dependent on face pose, lighting, occlusion, resolution, and detection quality.</li>
          <li>Real-world deployment requires additional adversarial privacy testing.</li>
          <li>Evaluation metrics are experimental indicators, not absolute measures.</li>
        </ul>
      </section>

    </div>
  );
};

export default About;
