import api from './api';
import type { FileUpload, PaginatedResponse, SearchParams } from '../utils/types.ts';
import qs from 'qs';

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

export const bulkUploadFiles = async (formData: FormData, onUploadProgress: (progressEvent: any) => void) => {
    const response = await api.post('/files/bulk-upload/', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
        onUploadProgress,
    });
    return response;
};

export const uploadFile = async (file: File, onUploadProgress: (progressEvent: any) => void) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('original_filename', file.name);
    console.log(formData, 'formData')
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

export const getFileTypes = async (): Promise<string[]> => {
    const response = await api.get<string[]>('/files/types/');
    return response.data;
};

export const searchFiles = async (params: SearchParams) => {
    const response = await api.get<PaginatedResponse<FileUpload>>('/files/', {
        params,
        paramsSerializer: params => {
            return qs.stringify(params, { arrayFormat: 'repeat' })
        }
    });
    return response.data;
};
