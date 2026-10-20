import { NavLink } from 'react-router-dom';
import { Shield, Cpu, Zap } from 'lucide-react';
import type { HealthStatus } from '../services/api';

interface NavbarProps {
  health: HealthStatus | null;
}

const Navbar = ({ health }: NavbarProps) => {
  const status = health?.status || 'offline';
  const isOnline = status === 'online';
  const isWarming = status === 'warming';
  const label = isOnline ? 'Operational' : isWarming ? 'Warming Up' : 'Offline';
  const inference = health?.inference || 'CPU';
  const isGpu = inference.toLowerCase().includes('gpu') || inference.toLowerCase().includes('directml');

  return (
    <header className="sticky top-0 z-50 w-full px-6 py-4">
      <div className="max-w-[1440px] mx-auto glass-panel px-6 py-3 flex items-center justify-between">
        
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-lg font-black tracking-wider text-slate-100 leading-tight">PRIVAI</h1>
              <p className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold leading-tight">Face Anonymization Platform</p>
            </div>
          </div>
          
          <div className="h-7 w-px bg-slate-800 mx-3 hidden md:block"></div>
          
          <nav className="hidden md:flex items-center gap-6 text-sm font-medium">
            <NavLink 
              to="/workspace" 
              className={({isActive}) => `transition-colors px-2 py-1 rounded-md ${isActive ? 'text-indigo-400 font-semibold' : 'text-slate-400 hover:text-slate-200'}`}
            >
              Studio
            </NavLink>
            <NavLink 
              to="/evaluation" 
              className={({isActive}) => `transition-colors px-2 py-1 rounded-md ${isActive ? 'text-indigo-400 font-semibold' : 'text-slate-400 hover:text-slate-200'}`}
            >
              Evaluation Lab
            </NavLink>
            <NavLink 
              to="/about" 
              className={({isActive}) => `transition-colors px-2 py-1 rounded-md ${isActive ? 'text-indigo-400 font-semibold' : 'text-slate-400 hover:text-slate-200'}`}
            >
              Architecture & Docs
            </NavLink>
          </nav>
        </div>

        <div className="flex items-center gap-3">
          {/* Hardware Engine Badge */}
          <div className={`hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border ${
            isGpu 
              ? 'bg-violet-500/10 text-violet-300 border-violet-500/30' 
              : 'bg-slate-800/80 text-slate-300 border-slate-700'
          }`}>
            {isGpu ? <Zap className="w-3.5 h-3.5 text-violet-400" /> : <Cpu className="w-3.5 h-3.5 text-slate-400" />}
            <span>{inference}</span>
          </div>

          {/* Operational Status */}
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold border ${
            isOnline 
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
              : isWarming 
                ? 'bg-amber-500/10 text-amber-300 border-amber-500/20' 
                : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
          }`}>
            <div className={`w-2 h-2 rounded-full ${
              isOnline ? 'bg-emerald-400 animate-pulse' : isWarming ? 'bg-amber-400' : 'bg-rose-400'
            }`}></div>
            {label}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
