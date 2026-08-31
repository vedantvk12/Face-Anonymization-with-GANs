import { useCallback, useState } from 'react';
import { UploadCloud, Image as ImageIcon } from 'lucide-react';

interface UploadPanelProps {
  onImageSelected: (file: File) => void;
  selectedImage: string | null;
}

const UploadPanel = ({ onImageSelected, selectedImage }: UploadPanelProps) => {
  const [isDragging, setIsDragging] = useState(false);

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
      onImageSelected(e.dataTransfer.files[0]);
    }
  }, [onImageSelected]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      onImageSelected(e.target.files[0]);
    }
  };

  return (
    <div className="glass-card p-6 h-full flex flex-col">
      <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
        <ImageIcon className="w-5 h-5 text-indigo-400" />
        Upload Image
      </h3>
      
      {!selectedImage ? (
        <div
          className={`flex-1 flex flex-col items-center justify-center border-2 border-dashed rounded-xl transition-all p-8 text-center ${
            isDragging 
              ? 'border-indigo-500 bg-indigo-500/10' 
              : 'border-slate-700 bg-slate-800/20 hover:bg-slate-800/40 hover:border-slate-600'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <UploadCloud className={`w-12 h-12 mb-4 ${isDragging ? 'text-indigo-400' : 'text-slate-500'}`} />
          <h4 className="text-lg font-medium text-slate-200 mb-2">Drag & drop your image here</h4>
          <p className="text-sm text-slate-500 mb-6">Supported: JPG, JPEG, PNG, WEBP</p>
          
          <label className="btn-secondary cursor-pointer">
            Browse Files
            <input 
              type="file" 
              className="hidden" 
              accept="image/jpeg, image/png, image/webp" 
              onChange={handleChange}
            />
          </label>
        </div>
      ) : (
        <div className="flex-1 flex flex-col relative group overflow-hidden rounded-xl border border-slate-700">
          <img src={selectedImage} alt="Preview" className="w-full h-full object-contain bg-slate-950/50" />
          <div className="absolute inset-0 bg-slate-900/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
             <label className="btn-secondary cursor-pointer">
              Change Image
              <input 
                type="file" 
                className="hidden" 
                accept="image/jpeg, image/png, image/webp" 
                onChange={handleChange}
              />
            </label>
          </div>
        </div>
      )}
    </div>
  );
};

export default UploadPanel;
