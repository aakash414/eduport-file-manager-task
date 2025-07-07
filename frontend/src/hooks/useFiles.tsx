// src/hooks/useFiles.tsx
import { useState, useEffect, useCallback } from 'react';
import { AxiosError } from 'axios';
import * as fileService from '../services/fileService';
import type { FileUpload, PaginatedResponse, SearchParams, ProgressEvent } from '../utils/types';

import { useToast } from './useToast';

export const useFiles = () => {
    const [fileData, setFileData] = useState<PaginatedResponse<FileUpload> | null>(null);
    const [loading, setLoading] = useState(true);
    const [progress, setProgress] = useState(0);
    const [uploadReport, setUploadReport] = useState<{ successful: any[]; failed: any[] } | null>(null);
    const { addToast } = useToast();

    const [currentSearchParams, setCurrentSearchParams] = useState<SearchParams>({});

    const searchFiles = useCallback(async (params: SearchParams) => {
        setLoading(true);
        // A new search resets pagination and stores the new filter state.
        const newSearch = { ...params };
        delete newSearch.cursor;
        delete newSearch.page;
        setCurrentSearchParams(newSearch);

        try {
            const data = await fileService.searchFiles(newSearch);
            setFileData(data);
        } catch (err) {
            addToast('Failed to fetch files.', 'error');
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [addToast]);

    // Handle pagination using cursor URLs
    const fetchPage = useCallback(async (url: string | null) => {
        if (!url) return;
        setLoading(true);
        try {
            const urlParams = new URL(url).searchParams;
            const paginationParams: SearchParams = {};
            const cursor = urlParams.get('cursor');
            if (cursor) {
                paginationParams.cursor = cursor;
            }
            const page = urlParams.get('page');
            if (page) {
                paginationParams.page = parseInt(page, 10);
            }

            // Combine the stored filters with the new page/cursor for the request.
            const paramsToFetch = { ...currentSearchParams, ...paginationParams };
            const data = await fileService.searchFiles(paramsToFetch);
            setFileData(data);
        } catch (err) {
            addToast('Failed to fetch page.', 'error');
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [addToast, currentSearchParams]);

    // Initial fetch on component mount.
    useEffect(() => {
        searchFiles({});
    }, [searchFiles]);

    const refreshCurrentView = useCallback(() => {
        searchFiles(currentSearchParams);
    }, [searchFiles, currentSearchParams]);

    const uploadFile = async (file: File) => {
        setLoading(true);
        setProgress(0);
        setUploadReport(null);

        try {
            const response = await fileService.uploadFile(file, (progressEvent: ProgressEvent) => {
                const percentCompleted = Math.round((progressEvent.loaded * 100) / (progressEvent.total ?? 1));
                setProgress(percentCompleted);
            });
            addToast('File uploaded successfully!', 'success');
            setUploadReport({ successful: [response], failed: [] });
            refreshCurrentView();
        } catch (err) {
            if (err instanceof AxiosError && err.response?.status === 409) {
                const errorData = err.response.data;
                addToast(errorData.detail || 'This file already exists.', 'error');
            } else {
                addToast('Failed to upload file.', 'error');
            }
            console.error(err);
        } finally {
            setLoading(false);
            setProgress(0);
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

    const bulkUploadFiles = async (files: File[]) => {
        setLoading(true);
        setProgress(0);
        setUploadReport(null);

        const formData = new FormData();
        files.forEach(file => formData.append('files', file));

        try {
            const response = await fileService.bulkUploadFiles(formData, (progressEvent: ProgressEvent) => {
                const percentCompleted = Math.round((progressEvent.loaded * 100) / (progressEvent.total ?? 1));
                setProgress(percentCompleted);
            });

            const { successful_uploads, failed_uploads, message } = response.data;

            // Show a summary toast
            addToast(message, failed_uploads.length > 0 ? 'warning' : 'success');

            // Show specific toasts for failures
            failed_uploads.forEach((failure: { filename: string; error: any }) => {
                const errorMessage = getErrorMessage(failure.error);
                addToast(`Failed: ${failure.filename} - ${errorMessage}`, 'error');
            });

            setUploadReport({ successful: successful_uploads, failed: failed_uploads });

            if (successful_uploads.length > 0) {
                refreshCurrentView();
            }

        } catch (err) {
            if (err instanceof AxiosError && err.response?.data) {
                const { failed_uploads, message } = err.response.data;
                addToast(message || 'An error occurred during bulk upload.', 'error');
                
                if (failed_uploads && Array.isArray(failed_uploads)) {
                    failed_uploads.forEach((failure: { filename: string; error: any }) => {
                        const errorMessage = getErrorMessage(failure.error);
                        addToast(`Failed: ${failure.filename} - ${errorMessage}`, 'error');
                    });
                }
            } else {
                addToast('A network or server error occurred.', 'error');
            }
            console.error(err);
        } finally {
            setLoading(false);
            setProgress(0);
        }
    };

    const deleteFile = async (fileId: number) => {
        try {
            await fileService.deleteFile(fileId);
            addToast('File deleted successfully.', 'success');
            refreshCurrentView();
        } catch (err) {
            addToast('Failed to delete file.', 'error');
            console.error(err);
        }
    };

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
    };
};
