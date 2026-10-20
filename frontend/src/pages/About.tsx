import Architecture from '../components/Architecture';
import { ShieldCheck, Layers, EyeOff } from 'lucide-react';

const About = () => {
  return (
    <div className="max-w-4xl mx-auto py-8 space-y-12 animate-in fade-in duration-500">
      
      <section className="space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold">
          <ShieldCheck className="w-4 h-4" />
          Enterprise Privacy Engineering
        </div>
        <h1 className="text-3xl font-black text-white">About PRIVAI Platform</h1>
        <p className="text-slate-300 leading-relaxed text-base max-w-3xl">
          PRIVAI is an enterprise-grade AI face anonymization platform engineered for privacy-preserving computer vision.
          It replaces identifiable facial biometric signatures in images and video streams with synthetic personas or artistic
          stylizations while preserving facial pose, expression, illumination, and complete environmental scene context.
        </p>
      </section>

      {/* Technical Pipeline Grid */}
      <section className="glass-card p-8">
        <h2 className="text-xl font-bold mb-6 text-slate-100 flex items-center gap-2">
          <Layers className="w-5 h-5 text-indigo-400" />
          Core Platform Technologies
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-800">
            <p className="text-xs text-indigo-400 uppercase tracking-wider font-bold mb-1">Face Detection & Alignment</p>
            <p className="font-semibold text-slate-200">InsightFace (SCRFD buffalo_l)</p>
            <p className="text-xs text-slate-400 mt-1">Multi-scale detection with 5-point facial landmark alignment</p>
          </div>
          
          <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-800">
            <p className="text-xs text-indigo-400 uppercase tracking-wider font-bold mb-1">Generative Replacement</p>
            <p className="font-semibold text-slate-200">InSwapper 128 GAN</p>
            <p className="text-xs text-slate-400 mt-1">ArcFace 512-d latent injection with high-fidelity seamless paste-back</p>
          </div>

          <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-800">
            <p className="text-xs text-indigo-400 uppercase tracking-wider font-bold mb-1">Stylization Pipelines</p>
            <p className="font-semibold text-slate-200">Cartoon & Anime Cel-Shading</p>
            <p className="text-xs text-slate-400 mt-1">Bilateral edge quantization and Japanese anime cel contours</p>
          </div>

          <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-800">
            <p className="text-xs text-indigo-400 uppercase tracking-wider font-bold mb-1">Video Multi-Face Tracker</p>
            <p className="font-semibold text-slate-200">IoU + Re-ID Embedding Memory</p>
            <p className="text-xs text-slate-400 mt-1">Consistent identity assignment across frames with jitter smoothing</p>
          </div>

          <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-800">
            <p className="text-xs text-indigo-400 uppercase tracking-wider font-bold mb-1">Audio & Codec Pipeline</p>
            <p className="font-semibold text-slate-200">FFmpeg 7.1 Multiplexer</p>
            <p className="text-xs text-slate-400 mt-1">Audio stream preservation & web-compatible H.264 YUV420p encoding</p>
          </div>

          <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-800">
            <p className="text-xs text-indigo-400 uppercase tracking-wider font-bold mb-1">Hardware Acceleration</p>
            <p className="font-semibold text-slate-200">NVIDIA RTX 4070 (DirectML / CUDA)</p>
            <p className="text-xs text-slate-400 mt-1">ONNX Runtime GPU inference with automated CPU fallback</p>
          </div>
        </div>
      </section>

      {/* System Architecture */}
      <section>
        <h2 className="text-xl font-bold mb-6 text-slate-100">System Architecture</h2>
        <Architecture />
      </section>

      {/* Privacy Limitations & Research Disclaimer */}
      <section className="glass-card p-8 border-rose-500/20 bg-rose-950/10">
        <h2 className="text-lg font-bold mb-3 text-rose-300 flex items-center gap-2">
          <EyeOff className="w-5 h-5 text-rose-400" />
          Privacy Assurance & Scientific Limitations
        </h2>
        <ul className="space-y-2.5 text-xs text-rose-200/90 list-disc pl-5 leading-relaxed">
          <li>
            <strong className="text-white">Identity Alteration Indicator:</strong> Low embedding cosine similarity indicates that deep face recognition feature extractors cannot correlate the output with the original person, but is not mathematical proof of zero re-identification.
          </li>
          <li>
            <strong className="text-white">Residual Biometrics:</strong> In extreme scenarios, secondary biometric signals (such as body stature, distinctive clothing, or gait in video) may permit inference unless contextual anonymization is also applied.
          </li>
          <li>
            <strong className="text-white">Lighting & Occlusion:</strong> Detection and swapping accuracy depend on face visibility, extreme yaw/pitch angles, and resolution.
          </li>
          <li>
            <strong className="text-white">Statutory Compliance:</strong> This software is designed for research, privacy preservation, and media obfuscation. Verify compliance with applicable data protection regulations (e.g. GDPR, CCPA) for your jurisdiction.
          </li>
        </ul>
      </section>

    </div>
  );
};

export default About;
