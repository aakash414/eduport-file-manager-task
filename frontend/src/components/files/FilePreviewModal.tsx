// src/components/files/FilePreviewModal.tsx
import React, { useEffect, useState } from 'react';
import apiClient from '../../api/axios';
import type { FileUpload } from '../../utils/types';
import LoadingSpinner from '../common/LoadingSpinner';

interface FilePreviewModalProps {
    fileId: number;
    onClose: () => void;
    onNext: () => void;
    onPrevious: () => void;
    hasNext: boolean;
    hasPrevious: boolean;
}

// Utility function to format file size
const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

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

const FilePreviewModal: React.FC<FilePreviewModalProps> = ({ fileId, onClose, onNext, onPrevious, hasNext, hasPrevious }) => {
    const [file, setFile] = useState<FileUpload | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [fileContent, setFileContent] = useState<string | null>(null);
    const [previewLoading, setPreviewLoading] = useState(false);
    const [isText, setIsText] = useState(false);

    useEffect(() => {
        if (!fileId) return;

        const abortController = new AbortController();
        let objectUrl: string | null = null;

        const fetchFileAndPreview = async () => {
            setLoading(true);
            setError(null);
            setFile(null);
            setFileContent(null);
            setIsText(false);

            try {
                // Fetch file details first
                const detailsResponse = await apiClient.get(`/api/files/${fileId}/`, {
                    signal: abortController.signal,
                });
                const fileDetails: FileUpload = detailsResponse.data;
                setFile(fileDetails);

                const mimeType = getMimeTypeFromFile(fileDetails);
                console.log(mimeType, 'mimeType')
                const isPreviewable =
                    mimeType.startsWith('image/') ||
                    mimeType.startsWith('video/') ||
                    mimeType.startsWith('audio/') ||
                    mimeType === 'application/pdf' ||
                    mimeType.startsWith('text/');
                console.log(file?.is_duplicate, 'is_duplicate')

                if (isPreviewable) {
                    setPreviewLoading(true);
                    try {
                        if (mimeType.startsWith('text/')) {
                            setIsText(true);
                            const previewResponse = await apiClient.get(`/api/files/${fileId}/content-preview/`, {
                                responseType: 'text',
                                signal: abortController.signal,
                            });
                            setFileContent(previewResponse.data);
                        } else {
                            const previewResponse = await apiClient.get(`/api/files/${fileId}/content-preview/`, {
                                responseType: 'blob',
                                signal: abortController.signal,
                            });
                            objectUrl = URL.createObjectURL(previewResponse.data);
                            console.log(objectUrl, 'objectUrl')
                            setFileContent(objectUrl);
                        }
                    } catch (previewError: any) {
                        if (previewError.name !== 'CanceledError') {
                            console.error('Failed to fetch file content:', previewError);
                            setError('Failed to load file preview.');
                        }
                    } finally {
                        setPreviewLoading(false);
                    }
                }
            } catch (err: any) {
                if (err.name !== 'CanceledError') {
                    console.error('Failed to fetch file details:', err);
                    setError('Failed to fetch file details.');
                }
            } finally {
                setLoading(false);
            }
        };

        fetchFileAndPreview();

        return () => {
            abortController.abort();
            if (objectUrl) {
                URL.revokeObjectURL(objectUrl);
            }
        };
    }, [fileId]);

    const handleDownload = async () => {
        if (!file) return;
        try {
            const response = await apiClient.get(`/api/files/${file.id}/download/`, {
                responseType: 'blob',
            });
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', file.original_filename || 'download');
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
        } catch (err) {
            console.error('Download failed:', err);
            setError('Failed to download file.');
        }
    };

    const renderFilePreview = () => {
        if (!file || !fileContent) {
            if (!error) {
                return (
                    <div className="text-center text-gray-500 py-8">
                        <p>No preview available for this file type.</p>
                        {file && <p className="text-sm mt-2">File type: {getMimeTypeFromFile(file) || 'Unknown'}</p>}
                    </div>
                );
            }
            return null;
        }

        const mimeType = getMimeTypeFromFile(file);
        if (mimeType.startsWith('image/')) {
            return <img src={fileContent} alt={file.original_filename} className="max-w-full max-h-[60vh] h-auto rounded-lg shadow-md mx-auto" />;
        }
        if (mimeType.startsWith('video/')) {
            return <video src={fileContent} controls className="max-w-full max-h-[60vh] h-auto rounded-lg shadow-md mx-auto">Your browser does not support the video tag.</video>;
        }
        if (mimeType.startsWith('audio/')) {
            return <audio src={fileContent} controls className="w-full max-w-md mx-auto">Your browser does not support the audio element.</audio>;
        }
        if (mimeType === 'application/pdf') {
            return <iframe src={fileContent} width="100%" height="600px" title={file.original_filename} className="border rounded-lg shadow-md" />;
        }
        if (isText) {
            return (
                <pre className="text-left whitespace-pre-wrap bg-white p-4 rounded-lg shadow-inner w-full h-full overflow-auto">
                    {fileContent}
                </pre>
            );
        }

        return <p>Preview not supported for this file type.</p>;
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-60 flex justify-center items-center z-50" onClick={onClose}>
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-6xl max-h-[95vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
                <header className="flex justify-between items-center p-4 border-b border-gray-200 bg-gray-50 rounded-t-xl">
                    <h2 className="text-xl font-bold text-gray-800 truncate pr-4" title={file?.original_filename}>
                        {file ? file.original_filename : 'Loading file...'}
                    </h2>
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <button onClick={onPrevious} disabled={!hasPrevious} className="p-2 rounded-full bg-gray-200 hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
                                <svg className="w-6 h-6 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
                            </button>
                            <button onClick={onNext} disabled={!hasNext} className="p-2 rounded-full bg-gray-200 hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
                                <svg className="w-6 h-6 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
                            </button>
                        </div>
                        <button onClick={onClose} className="p-2 rounded-full hover:bg-gray-300 transition-colors">
                            <svg className="w-6 h-6 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                        </button>
                    </div>
                </header>

                <main className="flex-grow overflow-y-auto py-6">
                    {loading && <div className="flex justify-center items-center h-64"><LoadingSpinner /></div>}
                    {error && <div className="text-center text-red-600 bg-red-50 p-4 rounded-lg">Error: {error}</div>}
                    {!loading && !error && file && (
                        <div className="flex flex-col lg:flex-row gap-6">
                            <div className="flex-grow flex justify-center items-center lg:w-2/3 bg-gray-100 rounded-lg p-4 min-h-[400px]">
                                {previewLoading ? <LoadingSpinner /> : renderFilePreview()}
                            </div>
                            <aside className="lg:w-1/3 flex-shrink-0">
                                <div className="bg-gray-50 p-4 rounded-lg border">
                                    <h3 className="text-lg font-semibold text-gray-800 border-b pb-2 mb-3">File Details</h3>
                                    <ul className="space-y-2 text-sm text-gray-600">
                                        <li><strong>Size:</strong> {formatFileSize(file.file_size)}</li>
                                        <li><strong>Type:</strong> {getMimeTypeFromFile(file) || 'Unknown'}</li>
                                        <li><strong>Uploaded:</strong> {new Date(file.upload_date).toLocaleString()}</li>
                                        <li ><strong>Last Accessed:</strong> {new Date(file.last_accessed).toLocaleString()}</li>
                                        <li><strong>Views:</strong> {file.view_count}</li>
                                        {file.is_duplicate && <li className="text-yellow-600 font-semibold">This is a duplicate file.</li>}
                                    </ul>
                                    {file.permissions?.can_download && (
                                        <button onClick={handleDownload} className="mt-4 w-full block text-center bg-indigo-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-indigo-700 transition-colors">
                                            Download
                                        </button>
                                    )}
                                </div>
                            </aside>
                        </div>
                    )}
                </main>

                <footer className="flex justify-end items-center pt-4 border-t border-gray-200">
                    <button onClick={onClose} className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors">
                        Close
                    </button>
                </footer>
            </div>
        </div>
    );
};

export default FilePreviewModal;