import { ShieldCheck, Eye, Cpu } from 'lucide-react';
import { motion } from 'framer-motion';

const Hero = () => {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="relative overflow-hidden rounded-[2rem] bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-800 shadow-2xl p-10 md:p-14 mb-8"
    >
      <div className="absolute top-0 right-0 w-1/2 h-full bg-gradient-to-l from-indigo-900/20 to-transparent pointer-events-none"></div>
      
      <div className="relative z-10 max-w-2xl">
        <h2 className="text-4xl md:text-6xl font-black tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-white via-slate-200 to-slate-400 mb-6 leading-[1.1]">
          Protect Identity.<br/>Preserve Utility.
        </h2>
        
        <p className="text-slate-400 text-base md:text-lg leading-relaxed mb-8 max-w-xl">
          Privacy-preserving face anonymization using synthetic identity replacement while maintaining the surrounding scene for downstream use.
        </p>

        <div className="flex flex-wrap items-center gap-4 mb-10">
          <button className="btn-primary" onClick={() => document.getElementById('upload-panel')?.scrollIntoView({ behavior: 'smooth'})}>
            Start Anonymizing
          </button>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/50 border border-slate-700/50 text-xs font-medium text-slate-300">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            Identity Protection
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/50 border border-slate-700/50 text-xs font-medium text-slate-300">
            <Eye className="w-4 h-4 text-sky-400" />
            Scene Preservation
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/50 border border-slate-700/50 text-xs font-medium text-slate-300">
            <Cpu className="w-4 h-4 text-indigo-400" />
            AI Processing
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default Hero;
