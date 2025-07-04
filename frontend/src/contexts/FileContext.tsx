// src/contexts/FileContext.tsx
import React, { createContext, useContext, ReactNode } from 'react';
import { useFiles } from '../hooks/useFiles';

interface FileContextType {
    fileData: ReturnType<typeof useFiles>['fileData'];
    loading: boolean;
    error: string | null;
    progress: number;
    fetchFiles: (page: number, search: string) => void;
    uploadFile: (file: File) => void;
    deleteFile: (fileId: number) => void;
}

const FileContext = createContext<FileContextType | undefined>(undefined);

export const FileProvider = ({ children }: { children: ReactNode }) => {
    const { fileData, loading, error, progress, fetchFiles, uploadFile, deleteFile } = useFiles();

    return (
        <FileContext.Provider value={{ fileData, loading, error, progress, fetchFiles, uploadFile, deleteFile }}>
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
