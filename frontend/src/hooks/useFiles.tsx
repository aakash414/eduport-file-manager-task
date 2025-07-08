import { useState, useEffect, useCallback, useRef } from 'react';
import api from '../services/api';
import * as fileService from '../services/fileService';
import type { FileUpload, PaginatedResponse, SearchParams, ProgressEvent } from '../utils/types';

import { useToast } from './useToast';
import { useAuth } from '../contexts/AuthContext';

export const useFiles = () => {
    const { isAuthenticated } = useAuth();
    const isAuthenticatedRef = useRef(isAuthenticated);
    isAuthenticatedRef.current = isAuthenticated;

    const [fileData, setFileData] = useState<PaginatedResponse<FileUpload> | null>(null);
    const [loading, setLoading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [uploadReport, setUploadReport] = useState<{ successful: any[]; failed: any[] } | null>(null);
    const { addToast } = useToast();

    const [currentSearchParams, setCurrentSearchParams] = useState<SearchParams>({});

    const clearFileData = useCallback(() => {
        setFileData(null);
    }, []);

    const searchFiles = useCallback(async (params: SearchParams) => {
        if (!isAuthenticatedRef.current) return;
        setLoading(true);
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

    const fetchPage = useCallback(async (url: string | null) => {
        if (!isAuthenticatedRef.current) return;
        if (!url) {
            return;
        }

        setLoading(true);
        try {
            const relativeUrl = new URL(url).pathname + new URL(url).search;

            const response = await api.get<PaginatedResponse<FileUpload>>(relativeUrl);
            setFileData(response.data);
        } catch (err) {
            console.error('Failed to fetch page:', err);
            addToast('Failed to fetch page.', 'error');
        } finally {
            setLoading(false);
        }
    }, [addToast]);

    const refreshCurrentView = useCallback(() => {
        searchFiles(currentSearchParams);
    }, [searchFiles, currentSearchParams]);

    const uploadFile = useCallback(async (file: File) => {
        if (!isAuthenticatedRef.current) return;

        const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
        if (file.size > MAX_FILE_SIZE) {
            addToast(`File size cannot exceed ${MAX_FILE_SIZE / 1024 / 1024}MB.`, 'error');
            return;
        }

        setLoading(true);
        setProgress(0);

        try {
            await fileService.uploadFile(file, (progressEvent: ProgressEvent) => {
                const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                setProgress(percentCompleted);
            });
            addToast('File uploaded successfully!', 'success');
            refreshCurrentView();
        } catch (err) {
            console.error('Failed to upload file:', err);
            addToast('Failed to upload file.', 'error');
        } finally {
            setLoading(false);
        }
    }, [addToast, refreshCurrentView]);

    const bulkUploadFiles = async (files: File[]) => {
        if (!isAuthenticatedRef.current) return;

        const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
        const validFiles = files.filter(file => {
            if (file.size > MAX_FILE_SIZE) {
                addToast(`'${file.name}' exceeds the size limit of 10MB and was not uploaded.`, 'error');
                return false;
            }
            return true;
        });

        if (validFiles.length === 0) {
            addToast('No valid files to upload.', 'warning');
            return;
        }

        setLoading(true);
        setProgress(0);
        setUploadReport(null);

        const formData = new FormData();
        validFiles.forEach(file => formData.append('files', file));

        try {
            const response = await fileService.bulkUploadFiles(formData, (progressEvent: ProgressEvent) => {
                const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                setProgress(percentCompleted);
            });

            addToast(response.data.message, 'success');

            setTimeout(() => {
                refreshCurrentView();
            }, 1000);
        } catch (err) {
            addToast('Bulk upload failed.', 'error');
            console.error(err);
        } finally {
            setLoading(false);
            setProgress(0);
        }
    };

    const deleteFile = async (fileId: number) => {
        if (!isAuthenticatedRef.current) return;
        try {
            await fileService.deleteFile(fileId);
            addToast('File deleted successfully.', 'success');
            refreshCurrentView();
        } catch (err) {
            addToast('Failed to delete file.', 'error');
            console.error(err);
        }
    };

    useEffect(() => {
        if (isAuthenticated) {
            searchFiles({});
        } else {
            clearFileData();
        }
    }, [isAuthenticated, searchFiles, clearFileData]);

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
        refreshCurrentView,
        clearFileData
    };
};
