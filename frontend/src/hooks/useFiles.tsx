// src/hooks/useFiles.tsx
import { useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import * as fileService from '../services/fileService';
import type { FileUpload, PaginatedResponse, SearchParams, ProgressEvent } from '../utils/types';

import { useToast } from './useToast';

export const useFiles = () => {
    const [fileData, setFileData] = useState<PaginatedResponse<FileUpload> | null>(null);
    const [loading, setLoading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [uploadReport, setUploadReport] = useState<{ successful: any[]; failed: any[] } | null>(null);
    const { addToast } = useToast();

    const [currentSearchParams, setCurrentSearchParams] = useState<SearchParams>({});

    const searchFiles = useCallback(async (params: SearchParams) => {
        setLoading(true);
        // A new search resets pagination and stores the new filter state.
        setCurrentSearchParams(params);

        try {
            const paginatedResponse = await fileService.searchFiles(params);
            setFileData(paginatedResponse);
        } catch (err) {
            console.error('Failed to fetch files:', err);
            addToast('Failed to fetch files.', 'error');
        } finally {
            setLoading(false);
        }
    }, [addToast]);

    const refreshCurrentView = useCallback(() => {
        const params = currentSearchParams;
        if (Object.keys(params).length > 0) {
            searchFiles(params);
        } else {
            fetchPage(null);
        }
    }, [searchFiles, currentSearchParams]);

    // Handle pagination using cursor URLs
    const fetchPage = useCallback(async (url: string | null) => {
        if (!url) {
            return;
        }

        try {
            const response = await api.get<PaginatedResponse<FileUpload>>(url);
            setFileData(response.data);
        } catch (err) {
            console.error('Failed to fetch page:', err);
            addToast('Failed to fetch page.', 'error');
        } finally {
            setLoading(false);
        }
    }, [addToast]);

    const uploadFile = useCallback(async (file: File) => {
        setLoading(true);
        setProgress(0);

        try {
            const response = await fileService.uploadFile(file, (progressEvent: ProgressEvent) => {
                const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                setProgress(percentCompleted);
            });
            setFileData(prev => prev ? { ...prev, results: [response, ...prev.results] } : { results: [response], count: 1, next: null, previous: null });
            addToast('File uploaded successfully!', 'success');
        } catch (err) {
            console.error('Failed to upload file:', err);
            addToast('Failed to upload file.', 'error');
        } finally {
            setLoading(false);
        }
    }, [addToast]);

    const bulkUploadFiles = async (files: File[]) => {
        setLoading(true);
        setProgress(0);
        setUploadReport(null);

        const formData = new FormData();
        files.forEach(file => formData.append('files', file));

        try {
            const response = await fileService.bulkUploadFiles(formData, (progressEvent: ProgressEvent) => {
                const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                setProgress(percentCompleted);
            });

            setFileData(prev => {
                if (!prev) return null;
                return {
                    ...prev,
                    results: [...response.data.successful_uploads, ...prev.results]
                };
            });

            const { failed_uploads, message } = response.data;

            // Show a summary toast
            addToast(message, failed_uploads.length > 0 ? 'warning' : 'success');

            // Show specific toasts for failures
            failed_uploads.forEach((failure: { filename: string; error: any }) => {
                const errorMessage = getErrorMessage(failure.error);
                addToast(`Failed: ${failure.filename} - ${errorMessage}`, 'error');
            });
        } catch (err) {
            addToast('Bulk upload failed.', 'error');
            console.error(err);
        } finally {
            setLoading(false);
            setProgress(0);
        }
    };

    const bulkDeleteFiles = async (fileIds: number[]) => {
        try {
            await fileService.bulkDeleteFiles(fileIds);
            addToast('Files deleted successfully.', 'success');
            refreshCurrentView();
        } catch (err) {
            addToast('Failed to delete files.', 'error');
            console.error(err);
        }
    };

    const deleteFile = async (fileId: number) => {
        try {
            await fileService.deleteFile(fileId);
            addToast('File deleted successfully.', 'success');
            setFileData(prev => {
                if (!prev) return null;
                return {
                    ...prev,
                    results: prev.results.filter(file => file.id !== fileId)
                };
            });
        } catch (err) {
            addToast('Failed to delete file.', 'error');
            console.error(err);
        }
    };

    const getErrorMessage = (error: any): string => {
        if (typeof error === 'string') {
            return error;
        }
        if (typeof error === 'object' && error !== null) {
            // This handles serializer errors which are often nested, e.g., { file: ["error message"] }
            const messages = Object.values(error).flat();
            return messages.join(' ');
        }
        return 'An unknown error occurred.';
    };

    // Initial fetch on component mount.
    useEffect(() => {
        searchFiles({});
    }, [searchFiles]);

    return {
        fileData,
        loading,
        progress,
        uploadReport,
        searchFiles,
        fetchPage,
        uploadFile,
        bulkUploadFiles,
        deleteFile,
        bulkDeleteFiles,
        refreshCurrentView
    };
};
