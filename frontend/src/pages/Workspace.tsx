import { useState, useEffect } from 'react';
import Hero from '../components/Hero';
import UploadPanel from '../components/UploadPanel';
import SettingsPanel from '../components/SettingsPanel';
import ResultViewer from '../components/ResultViewer';
import Metrics from '../components/Metrics';
import { getHealth, getSyntheticIdentities, anonymizeImage } from '../services/api';
import type { HealthStatus, AnonymizeResponse } from '../services/api';

const Workspace = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [identities, setIdentities] = useState<string[]>([]);
  
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  
  const [method, setMethod] = useState('generative');
  const [identity, setIdentity] = useState('random');
  
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState<AnonymizeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHealth().then(setHealth).catch(console.error);
    getSyntheticIdentities().then(res => setIdentities(res.identities)).catch(console.error);
  }, []);

  const handleImageSelected = (file: File) => {
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setResult(null);
    setError(null);
  };

  const handleAnonymize = async () => {
    if (!selectedFile) return;
    
    setIsProcessing(true);
    setError(null);
    
    try {
      const response = await anonymizeImage(selectedFile, method, identity);
      if (response.success) {
        setResult(response);
      }
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || "An error occurred during processing.");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="animate-in fade-in duration-500">
      <Hero />
      
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6" id="upload-panel">
        <div className="lg:col-span-8 min-h-[500px]">
          {!result ? (
            <UploadPanel 
              onImageSelected={handleImageSelected} 
              selectedImage={previewUrl} 
            />
          ) : (
            <ResultViewer 
              originalUrl={result.original_url}
              resultUrl={result.result_url}
              method={result.method}
            />
          )}
        </div>
        
        <div className="lg:col-span-4 min-h-[500px]">
          <SettingsPanel 
            method={method}
            setMethod={setMethod}
            identity={identity}
            setIdentity={setIdentity}
            identities={identities}
            health={health}
            onAnonymize={handleAnonymize}
            isProcessing={isProcessing}
            hasImage={!!selectedFile}
            loadingStateText={isProcessing ? "Generating anonymized image..." : undefined}
          />
        </div>
      </div>
      
      {error && (
        <div className="mt-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 font-medium text-sm flex items-start gap-3">
          <div className="w-5 h-5 rounded-full bg-rose-500/20 flex items-center justify-center shrink-0 mt-0.5">!</div>
          <p>{error}</p>
        </div>
      )}

      {(result || isProcessing) && (
        <Metrics 
          facesDetected={result ? result.faces_detected : null}
          processingTime={result ? result.processing_time : null}
        />
      )}
    </div>
  );
};

export default Workspace;
