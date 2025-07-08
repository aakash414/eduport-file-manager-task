import { createContext, useContext, type ReactNode } from 'react';
import { useFiles } from '../hooks/useFiles';
import type { SearchParams, FileUpload, PaginatedResponse } from '../utils/types';

interface FileContextType {
    fileData: PaginatedResponse<FileUpload> | null;
    loading: boolean;
    progress: number;
    uploadReport: { successful: any[]; failed: any[] } | null;
    uploadFile: (file: File) => Promise<void>;
    bulkUploadFiles: (files: File[]) => Promise<void>;
    deleteFile: (fileId: number) => Promise<void>;
    searchFiles: (params: SearchParams) => Promise<void>;
    fetchPage: (url: string | null) => Promise<void>;
    refreshCurrentView: () => void;
    clearFileData: () => void;
}

const FileContext = createContext<FileContextType | undefined>(undefined);

export const FileProvider = ({ children }: { children: ReactNode }) => {
    const {
        fileData,
        loading,
        progress,
        uploadReport,
        fetchPage,
        uploadFile,
        bulkUploadFiles,
        deleteFile,
        searchFiles,
        refreshCurrentView,
        clearFileData
    } = useFiles();

    return (
        <FileContext.Provider value={{
            fileData,
            loading,
            progress,
            uploadReport,
            fetchPage,
            uploadFile,
            bulkUploadFiles,
            deleteFile,
            searchFiles,
            refreshCurrentView,
            clearFileData
        }}>
            {children}
        </FileContext.Provider>
    );
};

export const useFileContext = () => {
    const context = useContext(FileContext);
    if (context === undefined) {
        throw new Error('useFileContext must be used within a FileProvider');
    }
    return context;
};
