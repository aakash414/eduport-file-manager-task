// src/contexts/FileContext.tsx
import { createContext, useContext, type ReactNode } from 'react';
import { useFiles } from '../hooks/useFiles';
import type { SearchParams } from '../utils/types';

interface FileContextType {
    fileData: ReturnType<typeof useFiles>['fileData'];
    loading: boolean;
    progress: number;
    uploadReport: { successful: any[]; failed: any[] } | null;
    fetchPage: (url: string | null) => void;
    uploadFile: (file: File) => void;
    bulkUploadFiles: (files: File[]) => void;
    deleteFile: (fileId: number) => void;
    searchFiles: (params: SearchParams) => void;
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
        searchFiles
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
            searchFiles
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
