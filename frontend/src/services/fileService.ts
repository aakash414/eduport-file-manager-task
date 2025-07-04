// src/services/fileService.ts
import api from './api';
import type { FileUpload, FileShareLink, PaginatedResponse } from '../utils/types.ts';

export const getFiles = async (page = 1, pageSize = 10, search = '') => {
    const response = await api.get<PaginatedResponse<FileUpload>>('/files/', {
        params: {
            page,
            page_size: pageSize,
            search,
        },
    });
    return response.data;
};

export const uploadFile = async (file: File, onUploadProgress: (progressEvent: any) => void) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('original_filename', file.name);

    const response = await api.post<FileUpload>('/files/upload/', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
        onUploadProgress,
    });
    return response.data;
};

export const getFileDetails = async (fileId: number) => {
    const response = await api.get<FileUpload>(`/files/${fileId}/`);
    return response.data;
};

export const updateFile = async (fileId: number, data: { description: string }) => {
    const response = await api.patch<FileUpload>(`/files/${fileId}/`, data);
    return response.data;
};

export const deleteFile = async (fileId: number) => {
    await api.delete(`/files/${fileId}/`);
};

export const bulkDeleteFiles = async (fileIds: number[]) => {
    const response = await api.post('/files/bulk-delete/', { file_ids: fileIds });
    return response.data;
};

export const downloadFile = async (fileId: number) => {
    const response = await api.get(`/files/${fileId}/download/`, {
        responseType: 'blob',
    });
    return response.data;
};

export const createFileShareLink = async (fileId: number, expires_at?: string) => {
    const response = await api.post<FileShareLink>('/files/share/', {
        file_upload: fileId,
        expires_at,
    });
    return response.data;
};

export const getFileShareLinks = async (fileId: number) => {
    const response = await api.get<FileShareLink[]>(`/files/${fileId}/share-links/`);
    return response.data;
};

export const deleteFileShareLink = async (linkId: number) => {
    await api.delete(`/files/share-links/${linkId}/`);
};

export const getFileStats = async () => {
    const response = await api.get('/files/stats/');
    return response.data;
};

export const cleanupOrphanedFiles = async (dryRun = false) => {
    const response = await api.post('/files/cleanup/orphaned/', { dry_run: dryRun });
    return response.data;
};

export const cleanupExpiredLinks = async (dryRun = false) => {
    const response = await api.post('/files/cleanup/expired-links/', { dry_run: dryRun });
    return response.data;
};

export const cleanupOldLogs = async (days: number, dryRun = false) => {
    const response = await api.post('/files/cleanup/old-logs/', { days, dry_run: dryRun });
    return response.data;
};
