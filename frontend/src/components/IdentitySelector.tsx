import { useState, useMemo } from 'react';
import { UserCheck, Shuffle } from 'lucide-react';
import type { SyntheticIdentity } from '../services/api';
import { getResultUrl } from '../services/api';

interface IdentitySelectorProps {
  identities: SyntheticIdentity[];
  selectedIdentity: string;
  onSelectIdentity: (id: string) => void;
  uniquePerPerson: boolean;
  onToggleUniquePerPerson: (val: boolean) => void;
}

const IdentitySelector = ({
  identities,
  selectedIdentity,
  onSelectIdentity,
  uniquePerPerson,
  onToggleUniquePerPerson
}: IdentitySelectorProps) => {
  const [styleFilter, setStyleFilter] = useState<string>('all');

  const filteredIdentities = useMemo(() => {
    if (styleFilter === 'all') return identities;
    return identities.filter(i => i.style.toLowerCase() === styleFilter.toLowerCase());
  }, [identities, styleFilter]);

  const stylePillColors: Record<string, string> = {
    realistic: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    cartoon: 'bg-amber-500/10 text-amber-300 border-amber-500/20',
    anime: 'bg-pink-500/10 text-pink-300 border-pink-500/20'
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label className="block text-sm font-semibold text-slate-200">
          Synthetic Identity Library
        </label>
        
        {/* Style tabs */}
        <div className="flex bg-slate-900/80 p-0.5 rounded-lg border border-slate-800 text-xs">
          {['all', 'realistic', 'cartoon', 'anime'].map((tab) => (
            <button
              key={tab}
              type="button"
              onClick={() => setStyleFilter(tab)}
              className={`px-2.5 py-1 rounded-md capitalize transition-all font-medium ${
                styleFilter === tab
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Identity Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 max-h-60 overflow-y-auto pr-1 custom-scrollbar">
        {/* Random / Auto Option */}
        <button
          type="button"
          onClick={() => onSelectIdentity('random')}
          className={`flex items-center gap-3 p-2.5 rounded-xl border text-left transition-all ${
            selectedIdentity === 'random'
              ? 'bg-indigo-600/20 border-indigo-500 ring-1 ring-indigo-500'
              : 'bg-slate-900/60 border-slate-800 hover:bg-slate-800/60'
          }`}
        >
          <div className="w-11 h-11 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center shrink-0 text-indigo-400">
            <Shuffle className="w-5 h-5" />
          </div>
          <div className="overflow-hidden">
            <p className="text-xs font-bold text-slate-200 truncate">Random Persona</p>
            <p className="text-[10px] text-slate-400 truncate">Dynamic cycling</p>
          </div>
        </button>

        {/* Identity Cards */}
        {filteredIdentities.map((item) => {
          const isSelected = selectedIdentity === item.id;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onSelectIdentity(item.id)}
              className={`flex items-center gap-2.5 p-2 rounded-xl border text-left transition-all relative overflow-hidden group ${
                isSelected
                  ? 'bg-indigo-600/20 border-indigo-500 ring-1 ring-indigo-500 shadow-[0_0_15px_rgba(99,102,241,0.15)]'
                  : 'bg-slate-900/60 border-slate-800 hover:bg-slate-800/60'
              }`}
            >
              <img
                src={getResultUrl(item.thumbnail)}
                alt={item.name}
                className="w-11 h-11 rounded-lg object-cover bg-slate-950 shrink-0 border border-slate-700/60"
                onError={(e) => {
                  // Fallback avatar placeholder
                  (e.target as HTMLElement).style.display = 'none';
                }}
              />
              <div className="overflow-hidden">
                <p className="text-xs font-bold text-slate-200 truncate flex items-center gap-1">
                  {item.name}
                </p>
                <span className={`inline-block text-[9px] px-1.5 py-0.2 rounded border font-semibold mt-0.5 ${stylePillColors[item.style] || 'bg-slate-800 text-slate-400'}`}>
                  {item.style}
                </span>
              </div>
              {isSelected && (
                <div className="absolute top-1.5 right-1.5 w-4 h-4 rounded-full bg-indigo-500 flex items-center justify-center text-white">
                  <UserCheck className="w-2.5 h-2.5" />
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Multi-person assignment option */}
      <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs">
        <span className="text-slate-300 font-medium">Distinct identity per person</span>
        <label className="relative inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            checked={uniquePerPerson}
            onChange={(e) => onToggleUniquePerPerson(e.target.checked)}
            className="sr-only peer"
          />
          <div className="w-9 h-5 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-indigo-600"></div>
        </label>
      </div>
    </div>
  );
};

export default IdentitySelector;
