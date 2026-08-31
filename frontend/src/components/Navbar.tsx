import { NavLink } from 'react-router-dom';
import { Shield } from 'lucide-react';
import type { HealthStatus } from '../services/api';

interface NavbarProps {
  health: HealthStatus | null;
}

const Navbar = ({ health }: NavbarProps) => {
  return (
    <header className="sticky top-0 z-50 w-full px-6 py-4">
      <div className="max-w-[1400px] mx-auto glass-panel px-6 py-3 flex items-center justify-between">
        
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Shield className="w-6 h-6 text-indigo-400" />
            <div>
              <h1 className="text-lg font-black tracking-widest text-slate-100 leading-tight">PRIVAI</h1>
              <p className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold leading-tight">AI Face Anonymization</p>
            </div>
          </div>
          
          <div className="h-8 w-px bg-slate-700/50 mx-4 hidden md:block"></div>
          
          <nav className="hidden md:flex items-center gap-6 text-sm font-medium">
            <NavLink 
              to="/workspace" 
              className={({isActive}) => `transition-colors ${isActive ? 'text-indigo-400' : 'text-slate-400 hover:text-slate-200'}`}
            >
              Workspace
            </NavLink>
            <NavLink 
              to="/evaluation" 
              className={({isActive}) => `transition-colors ${isActive ? 'text-indigo-400' : 'text-slate-400 hover:text-slate-200'}`}
            >
              Evaluation
            </NavLink>
            <NavLink 
              to="/about" 
              className={({isActive}) => `transition-colors ${isActive ? 'text-indigo-400' : 'text-slate-400 hover:text-slate-200'}`}
            >
              About
            </NavLink>
          </nav>
        </div>

        <div className="flex items-center gap-3">
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold border ${health?.status === 'online' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border-rose-500/20'}`}>
            <div className={`w-2 h-2 rounded-full ${health?.status === 'online' ? 'bg-emerald-400' : 'bg-rose-400'}`}></div>
            {health?.status === 'online' ? 'Operational' : 'Offline'}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
