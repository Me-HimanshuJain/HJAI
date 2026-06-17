import React, { useState, useRef } from 'react';
import { uploadDocument, uploadImage, uploadAudio } from '@/lib/api';

export default function MediaUploader({ userId }: { userId: string }) {
  const [isUploading, setIsUploading] = useState(false);
  const [lastUploadStatus, setLastUploadStatus] = useState<{type: string, msg: string} | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setLastUploadStatus(null);
    
    try {
      if (file.type.startsWith('image/')) {
        const res = await uploadImage(file);
        setLastUploadStatus({ type: 'success', msg: `OCR: Extracted text` });
      } else if (file.type.startsWith('audio/')) {
        const res = await uploadAudio(file);
        setLastUploadStatus({ type: 'success', msg: `STT: Transcribed audio` });
      } else {
        // Assume document (pdf, docx, txt)
        const res = await uploadDocument(userId, file);
        setLastUploadStatus({ type: 'success', msg: `RAG: Vectorized ${res.chunks_processed} chunks` });
      }
    } catch (err) {
      console.error(err);
      setLastUploadStatus({ type: 'error', msg: 'Upload failed' });
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  return (
    <div>
      <input 
        type="file" 
        className="hidden" 
        ref={fileInputRef} 
        onChange={handleFileChange} 
        accept=".pdf,.docx,.txt,image/*,audio/*"
      />
      <button 
        onClick={() => fileInputRef.current?.click()}
        disabled={isUploading}
        className="w-full py-6 px-4 border border-dashed border-zinc-700 hover:border-[#2563EB] hover:bg-[#2563EB]/5 rounded-xl transition-all flex flex-col items-center justify-center gap-2 group disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-zinc-500 group-hover:text-[#2563EB] transition-colors"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
        <span className="text-xs text-zinc-400 group-hover:text-zinc-300">
          {isUploading ? 'Processing...' : 'Upload PDF, DOCX, IMG, Audio'}
        </span>
      </button>

      {lastUploadStatus && (
        <div className={`mt-3 text-xs p-2 rounded border ${lastUploadStatus.type === 'success' ? 'bg-emerald-900/20 border-emerald-900/50 text-emerald-400' : 'bg-red-900/20 border-red-900/50 text-red-400'}`}>
          {lastUploadStatus.msg}
        </div>
      )}
    </div>
  );
}
