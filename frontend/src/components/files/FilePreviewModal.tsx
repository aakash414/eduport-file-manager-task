// src/components/files/FilePreviewModal.tsx
import React, { useEffect } from 'react';
import type { FileUpload } from '../../utils/types';

interface FilePreviewModalProps {
    files: FileUpload[];
    currentIndex: number;
    onClose: () => void;
    onNext: () => void;
    onPrevious: () => void;
}

const getMimeTypeFromFile = (file: FileUpload): string => {
    const fileType = file.file_type?.toLowerCase() || '';
    const filename = file.original_filename?.toLowerCase() || '';
    const extension = filename.split('.').pop() || '';

    if (fileType.includes('/')) {
        return fileType;
    }

    const ext = fileType || extension;

    switch (ext) {
        case 'jpg':
        case 'jpeg':
            return 'image/jpeg';
        case 'png':
            return 'image/png';
        case 'gif':
            return 'image/gif';
        case 'svg':
            return 'image/svg+xml';
        case 'webp':
            return 'image/webp';
        case 'mp4':
            return 'video/mp4';
        case 'webm':
            return 'video/webm';
        case 'ogv':
            return 'video/ogg';
        case 'mp3':
            return 'audio/mpeg';
        case 'wav':
            return 'audio/wav';
        case 'oga':
            return 'audio/ogg';
        case 'pdf':
            return 'application/pdf';
        case 'txt':
            return 'text/plain';
        case 'csv':
            return 'text/csv';
        case 'md':
            return 'text/markdown';
        default:
            if (['xml', 'html', 'css', 'js', 'json'].includes(ext)) {
                return `text/${ext}`;
            }
            return fileType;
    }
};

const FilePreviewModal: React.FC<FilePreviewModalProps> = ({ files, currentIndex, onClose, onNext, onPrevious }) => {
    const file = files[currentIndex];
    const hasNext = currentIndex < files.length - 1;
    const hasPrevious = currentIndex > 0;

    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'ArrowRight' && hasNext) {
                onNext();
            } else if (e.key === 'ArrowLeft' && hasPrevious) {
                onPrevious();
            } else if (e.key === 'Escape') {
                onClose();
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => {
            window.removeEventListener('keydown', handleKeyDown);
        };
    }, [onNext, onPrevious, onClose, hasNext, hasPrevious]);

    const handleDownload = () => {
        if (!file?.file_url) return;
        const link = document.createElement('a');
        link.href = file.file_url;
        link.setAttribute('download', file.original_filename || 'download');
        document.body.appendChild(link);
        link.click();
        link.remove();
    };

    const renderFilePreview = () => {
        if (!file || !file.file_url) {
            return (
                <div className="text-center text-gray-500 py-8">
                    <p>No preview available for this file.</p>
                </div>
            );
        }

        const mimeType = getMimeTypeFromFile(file);
        const fileUrl = file.file_url;

        if (mimeType.startsWith('image/')) {
            return <img src={fileUrl} alt={file.original_filename} className="max-w-full max-h-[70vh] h-auto rounded-lg shadow-md mx-auto" />;
        }
        if (mimeType.startsWith('video/')) {
            return <video src={fileUrl} controls className="max-w-full max-h-[70vh] rounded-lg shadow-md mx-auto" />;
        }
        if (mimeType.startsWith('audio/')) {
            return <audio src={fileUrl} controls className="w-full mt-4" />;
        }
        if (mimeType === 'application/pdf' || mimeType.startsWith('text/')) {
            return <iframe src={fileUrl} title={file.original_filename} className="w-full h-[75vh] border-0 rounded-lg shadow-md bg-white" />;
        }

        return (
            <div className="text-center text-gray-500 py-8">
                <p>Preview not supported for this file type.</p>
                <p className="text-sm mt-2">File type: {mimeType || 'Unknown'}</p>
                <button onClick={handleDownload} className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700">
                    Download File
                </button>
            </div>
        );
    };

    if (!file) {
        return null; // Or a loading/error state if currentIndex is out of bounds
    }

    return (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4" onClick={onClose}>
            {/* Previous Button */}
            {hasPrevious && (
                <button
                    onClick={(e) => { e.stopPropagation(); onPrevious(); }}
                    className="absolute left-4 top-1/2 -translate-y-1/2 p-2 text-white bg-black bg-opacity-50 rounded-full hover:bg-opacity-75 focus:outline-none z-10"
                    title="Previous (Left Arrow)"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
                </button>
            )}

            <div className="bg-gray-800 rounded-lg shadow-2xl w-full max-w-5xl max-h-[90vh] flex flex-col relative" onClick={(e) => e.stopPropagation()}>
                <header className="flex items-center justify-between p-4 border-b border-gray-700">
                    <div className="min-w-0 flex-1">
                        <h2 className="text-lg font-semibold text-white truncate">{file.original_filename}</h2>
                        <p className="text-sm text-gray-400">{file.file_size_display}</p>
                    </div>
                    <div className="flex items-center space-x-2">
                        <button onClick={handleDownload} className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-full" title="Download">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                        </button>
                        <button onClick={onClose} className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-full" title="Close (Esc)">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                        </button>
                    </div>
                </header>

                <main className="flex-1 p-4 bg-gray-900 overflow-y-auto flex items-center justify-center">
                    {renderFilePreview()}
                </main>
            </div>

            {/* Next Button */}
            {hasNext && (
                <button
                    onClick={(e) => { e.stopPropagation(); onNext(); }}
                    className="absolute right-4 top-1/2 -translate-y-1/2 p-2 text-white bg-black bg-opacity-50 rounded-full hover:bg-opacity-75 focus:outline-none z-10"
                    title="Next (Right Arrow)"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
                </button>
            )}
        </div>
    );
};

export default FilePreviewModal;
