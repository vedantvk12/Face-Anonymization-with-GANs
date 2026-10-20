import { useCallback, useState } from 'react';
import { UploadCloud, Image as ImageIcon, Film, FileVideo } from 'lucide-react';

interface UploadPanelProps {
  mode: 'image' | 'video';
  onFileSelected: (file: File) => void;
  selectedFile: File | null;
  previewUrl: string | null;
  onClear: () => void;
}

const UploadPanel = ({ mode, onFileSelected, selectedFile, previewUrl, onClear }: UploadPanelProps) => {
  const [isDragging, setIsDragging] = useState(false);

  const acceptedTypes = mode === 'image' 
    ? 'image/jpeg, image/png, image/webp' 
    : 'video/mp4, video/quicktime, video/x-msvideo';

  const formatText = mode === 'image' ? 'JPG, JPEG, PNG, WEBP' : 'MP4, MOV, AVI';

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragging(true);
    } else if (e.type === 'dragleave') {
      setIsDragging(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileSelected(e.dataTransfer.files[0]);
    }
  }, [onFileSelected]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      onFileSelected(e.target.files[0]);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="glass-card p-6 h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold flex items-center gap-2 text-slate-100">
          {mode === 'image' ? (
            <ImageIcon className="w-5 h-5 text-indigo-400" />
          ) : (
            <Film className="w-5 h-5 text-indigo-400" />
          )}
          Source {mode === 'image' ? 'Image' : 'Video'}
        </h3>

        {selectedFile && (
          <span className="text-xs px-2.5 py-1 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
            {formatFileSize(selectedFile.size)}
          </span>
        )}
      </div>

      {!previewUrl ? (
        <div
          className={`flex-1 flex flex-col items-center justify-center border-2 border-dashed rounded-xl transition-all p-8 text-center ${
            isDragging
              ? 'border-indigo-500 bg-indigo-500/10'
              : 'border-slate-800 bg-slate-900/30 hover:bg-slate-900/50 hover:border-slate-700'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <div className="w-16 h-16 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center mb-4 text-indigo-400">
            {mode === 'image' ? (
              <UploadCloud className="w-8 h-8" />
            ) : (
              <FileVideo className="w-8 h-8" />
            )}
          </div>
          <h4 className="text-base font-semibold text-slate-200 mb-1">
            Drag & drop your {mode} here
          </h4>
          <p className="text-xs text-slate-400 mb-5">Supported formats: {formatText}</p>

          <label className="btn-secondary cursor-pointer py-2 px-5 text-sm">
            Browse {mode === 'image' ? 'Images' : 'Videos'}
            <input
              type="file"
              className="hidden"
              accept={acceptedTypes}
              onChange={handleChange}
            />
          </label>
        </div>
      ) : (
        <div className="flex-1 flex flex-col relative group overflow-hidden rounded-xl border border-slate-800 bg-slate-950 flex items-center justify-center p-2">
          {mode === 'image' ? (
            <img
              src={previewUrl}
              alt="Preview"
              className="max-w-full max-h-[440px] object-contain rounded-lg"
            />
          ) : (
            <video
              src={previewUrl}
              controls
              className="max-w-full max-h-[440px] rounded-lg"
            />
          )}

          <div className="absolute top-4 right-4 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <label className="px-3 py-1.5 rounded-lg bg-slate-900/90 hover:bg-slate-800 text-slate-200 text-xs font-semibold border border-slate-700 cursor-pointer shadow-lg backdrop-blur">
              Replace
              <input
                type="file"
                className="hidden"
                accept={acceptedTypes}
                onChange={handleChange}
              />
            </label>
            <button
              type="button"
              onClick={onClear}
              className="px-3 py-1.5 rounded-lg bg-rose-950/80 hover:bg-rose-900 text-rose-300 text-xs font-semibold border border-rose-800/80 shadow-lg backdrop-blur"
            >
              Clear
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default UploadPanel;
