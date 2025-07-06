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

    // Store the base search parameters, without pagination cursors.
    const [baseSearchParams, setBaseSearchParams] = useState<SearchParams>({});

    const searchFiles = useCallback(async (params: SearchParams) => {
        setLoading(true);
        // If this is a new search (no cursor), update the base search params.
        if (params.cursor === undefined) {
            const { page, page_size, ...baseParams } = params;
            setBaseSearchParams(baseParams);
        }
        try {
            const data = await fileService.searchFiles(params);
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
            const params: SearchParams = {};
            for (const [key, value] of urlParams.entries()) {
                params[key] = value;
            }
            // searchFiles will call the service and update state
            await searchFiles(params);
        } catch (err) {
            addToast('Failed to fetch page.', 'error');
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [searchFiles, addToast]);

    // Initial fetch
    useEffect(() => {
        searchFiles({});
    }, [searchFiles]);

    const refreshCurrentView = useCallback(() => {
        // Refresh by re-running the base search, which gets the first page.
        searchFiles(baseSearchParams);
    }, [searchFiles, baseSearchParams]);

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

    const bulkUploadFiles = async (files: File[]) => {
        setLoading(true);
        setProgress(0);
        setUploadReport(null);

        try {
            const formData = new FormData();
            for (let i = 0; i < files.length; i++) {
                formData.append('files', files[i]);
            }
            const response = await fileService.bulkUploadFiles(formData, (progressEvent: ProgressEvent) => {
                const percentCompleted = Math.round((progressEvent.loaded * 100) / (progressEvent.total ?? 1));
                setProgress(percentCompleted);
            });
            addToast(response.data.message, 'success');
            setUploadReport({
                successful: response.data.successful_uploads,
                failed: response.data.failed_uploads
            });
            refreshCurrentView();
        } catch (err) {
            addToast('Failed to upload files.', 'error');
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
            // After deleting, refresh the list using the base search parameters.
            // This will show the first page of the current search.
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
