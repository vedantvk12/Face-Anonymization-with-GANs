import { useState, useEffect, useRef } from 'react';
import Hero from '../components/Hero';
import UploadPanel from '../components/UploadPanel';
import SettingsPanel from '../components/SettingsPanel';
import ResultViewer from '../components/ResultViewer';
import VideoProgress from '../components/VideoProgress';
import Metrics from '../components/Metrics';
import {
  DEFAULT_HEALTH_STATUS,
  getHealth,
  getIdentities,
  anonymizeImage,
  anonymizeVideo,
  getVideoStatus,
  cancelVideoJob
} from '../services/api';
import type {
  HealthStatus,
  SyntheticIdentity,
  AnonymizeResponse,
  VideoJobStatus
} from '../services/api';
import { Image as ImageIcon, Film } from 'lucide-react';

const Workspace = () => {
  const [mode, setMode] = useState<'image' | 'video'>('image');
  const [health, setHealth] = useState<HealthStatus>(DEFAULT_HEALTH_STATUS);
  const [identities, setIdentities] = useState<SyntheticIdentity[]>([]);

  // Media selection
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  // Configuration
  const [method, setMethod] = useState('generative');
  const [identity, setIdentity] = useState('random');
  const [resolution, setResolution] = useState('original');
  const [uniquePerPerson, setUniquePerPerson] = useState(true);

  // Processing state
  const [isProcessing, setIsProcessing] = useState(false);
  const [imageResult, setImageResult] = useState<AnonymizeResponse | null>(null);
  const [videoJob, setVideoJob] = useState<VideoJobStatus | null>(null);
  const [isCancelling, setIsCancelling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const pollIntervalRef = useRef<number | null>(null);

  useEffect(() => {
    getHealth().then(setHealth).catch(console.error);
    getIdentities().then(res => setIdentities(res.identities)).catch(console.error);
  }, []);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        window.clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  const handleModeChange = (newMode: 'image' | 'video') => {
    if (isProcessing) return;
    setMode(newMode);
    setSelectedFile(null);
    setPreviewUrl(null);
    setImageResult(null);
    setVideoJob(null);
    setError(null);
  };

  const handleFileSelected = (file: File) => {
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setImageResult(null);
    setVideoJob(null);
    setError(null);
  };

  const handleClearFile = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setImageResult(null);
    setVideoJob(null);
    setError(null);
  };

  // Image Anonymization
  const handleAnonymizeImage = async () => {
    if (!selectedFile) return;
    setIsProcessing(true);
    setError(null);

    try {
      const response = await anonymizeImage(selectedFile, method, identity, uniquePerPerson);
      if (response.success) {
        setImageResult(response);
      }
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || "An error occurred during image processing.");
    } finally {
      setIsProcessing(false);
    }
  };

  // Video Anonymization with background polling
  const handleAnonymizeVideo = async () => {
    if (!selectedFile) return;
    setIsProcessing(true);
    setError(null);

    try {
      const initRes = await anonymizeVideo(selectedFile, method, identity, resolution);
      const jobId = initRes.job_id;

      // Start polling status
      pollIntervalRef.current = window.setInterval(async () => {
        try {
          const status = await getVideoStatus(jobId);
          setVideoJob(status);

          if (status.status === 'completed') {
            setIsProcessing(false);
            if (pollIntervalRef.current) {
              window.clearInterval(pollIntervalRef.current);
              pollIntervalRef.current = null;
            }
          } else if (status.status === 'failed') {
            setIsProcessing(false);
            setError(status.error_message || "Video processing encountered an error.");
            if (pollIntervalRef.current) {
              window.clearInterval(pollIntervalRef.current);
              pollIntervalRef.current = null;
            }
          } else if (status.status === 'cancelled') {
            setIsProcessing(false);
            setError("Video processing was cancelled by user.");
            if (pollIntervalRef.current) {
              window.clearInterval(pollIntervalRef.current);
              pollIntervalRef.current = null;
            }
          }
        } catch (pollErr: any) {
          console.error("Polling error:", pollErr);
        }
      }, 700);

    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || "Failed to start video processing.");
      setIsProcessing(false);
    }
  };

  const handleCancelVideo = async () => {
    if (!videoJob) return;
    setIsCancelling(true);
    try {
      await cancelVideoJob(videoJob.id);
    } catch (err) {
      console.error("Cancel failed:", err);
    } finally {
      setIsCancelling(false);
    }
  };

  const handleTriggerProcessing = () => {
    if (mode === 'image') {
      handleAnonymizeImage();
    } else {
      handleAnonymizeVideo();
    }
  };

  const isVideoCompleted = videoJob?.status === 'completed';
  const showResultViewer = mode === 'image' ? !!imageResult : isVideoCompleted;

  return (
    <div className="animate-in fade-in duration-500 space-y-6">
      <Hero />

      {/* Mode Switcher Tabs */}
      <div className="flex items-center justify-center">
        <div className="bg-slate-900/90 p-1 rounded-2xl border border-slate-800 shadow-xl flex gap-1">
          <button
            type="button"
            onClick={() => handleModeChange('image')}
            disabled={isProcessing}
            className={`flex items-center gap-2 px-6 py-2.5 rounded-xl font-bold text-sm transition-all ${
              mode === 'image'
                ? 'bg-indigo-600 text-white shadow-[0_0_15px_rgba(99,102,241,0.3)]'
                : 'text-slate-400 hover:text-slate-200 disabled:opacity-50'
            }`}
          >
            <ImageIcon className="w-4 h-4" />
            Image Studio
          </button>

          <button
            type="button"
            onClick={() => handleModeChange('video')}
            disabled={isProcessing}
            className={`flex items-center gap-2 px-6 py-2.5 rounded-xl font-bold text-sm transition-all ${
              mode === 'video'
                ? 'bg-indigo-600 text-white shadow-[0_0_15px_rgba(99,102,241,0.3)]'
                : 'text-slate-400 hover:text-slate-200 disabled:opacity-50'
            }`}
          >
            <Film className="w-4 h-4" />
            Video Studio
          </button>
        </div>
      </div>

      {/* Video Progress Bar (when video is actively processing) */}
      {mode === 'video' && isProcessing && videoJob && (
        <VideoProgress
          status={videoJob}
          onCancel={handleCancelVideo}
          isCancelling={isCancelling}
        />
      )}

      {/* Main Workspace Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6" id="upload-panel">
        <div className="lg:col-span-8 min-h-[520px]">
          {!showResultViewer ? (
            <UploadPanel
              mode={mode}
              onFileSelected={handleFileSelected}
              selectedFile={selectedFile}
              previewUrl={previewUrl}
              onClear={handleClearFile}
            />
          ) : (
            <ResultViewer
              type={mode}
              originalUrl={mode === 'image' ? imageResult!.original_url : videoJob!.original_url!}
              resultUrl={mode === 'image' ? imageResult!.result_url : videoJob!.result_url!}
              method={mode === 'image' ? imageResult!.method : videoJob!.method}
              syntheticIdentity={mode === 'image' ? imageResult?.synthetic_identity : videoJob?.identity}
              onReset={handleClearFile}
            />
          )}
        </div>

        <div className="lg:col-span-4 min-h-[520px]">
          <SettingsPanel
            mode={mode}
            method={method}
            setMethod={setMethod}
            identity={identity}
            setIdentity={setIdentity}
            identities={identities}
            resolution={resolution}
            setResolution={setResolution}
            uniquePerPerson={uniquePerPerson}
            setUniquePerPerson={setUniquePerPerson}
            health={health}
            onAnonymize={handleTriggerProcessing}
            isProcessing={isProcessing}
            hasFile={!!selectedFile}
            loadingStateText={
              isProcessing
                ? mode === 'image'
                  ? 'Anonymizing image...'
                  : 'Processing video frames...'
                : undefined
            }
          />
        </div>
      </div>

      {/* Error alert */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 font-medium text-sm flex items-start gap-3">
          <div className="w-5 h-5 rounded-full bg-rose-500/20 flex items-center justify-center shrink-0 mt-0.5 font-bold">
            !
          </div>
          <p>{error}</p>
        </div>
      )}

      {/* Real Performance Metrics */}
      {(showResultViewer || isProcessing) && (
        <Metrics
          facesDetected={
            mode === 'image'
              ? imageResult?.faces_detected ?? null
              : videoJob?.status === 'completed'
                ? 1
                : null
          }
          processingTime={
            mode === 'image'
              ? imageResult?.processing_time ?? null
              : videoJob?.elapsed_time ?? null
          }
          fps={mode === 'video' ? videoJob?.fps ?? null : null}
          totalFrames={mode === 'video' ? videoJob?.total_frames ?? null : null}
          hardware={health.inference}
          runId={mode === 'image' ? imageResult?.run_id : videoJob?.id}
        />
      )}
    </div>
  );
};

export default Workspace;
