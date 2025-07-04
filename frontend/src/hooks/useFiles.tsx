// src/hooks/useFiles.tsx
import { useState, useEffect, useCallback } from 'react';
import * as fileService from '../services/fileService';
import type { FileUpload, PaginatedResponse } from '../utils/types';

export const useFiles = (page = 1, pageSize = 10) => {
    const [fileData, setFileData] = useState<PaginatedResponse<FileUpload> | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [progress, setProgress] = useState(0);

    const fetchFiles = useCallback(async (currentPage: number, currentSearch: string) => {
        setLoading(true);
        try {
            const data = await fileService.getFiles(currentPage, pageSize, currentSearch);
            setFileData(data);
        } catch (err) {
            setError('Failed to fetch files.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [page, pageSize]);

    useEffect(() => {
        fetchFiles(page, '');
    }, [fetchFiles, page]);

    const uploadFile = async (file: File) => {
        setLoading(true);
        setProgress(0);
        try {
            await fileService.uploadFile(file, (progressEvent) => {
                const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                setProgress(percentCompleted);
            });
            // Refresh file list after upload
            fetchFiles(page, '');
        } catch (err) {
            setError('Failed to upload file.');
            console.error(err);
        } finally {
            setLoading(false);
            setProgress(0);
        }
    };

    const deleteFile = async (fileId: number) => {
        setLoading(true);
        try {
            await fileService.deleteFile(fileId);
            // Refresh file list after delete
            fetchFiles(page, '');
        } catch (err) {
            setError('Failed to delete file.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return {
        fileData,
        loading,
        error,
        progress,
        fetchFiles,
        uploadFile,
        deleteFile,
    };
};
