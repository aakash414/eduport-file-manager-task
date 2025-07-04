// src/components/files/FileItem.tsx
import React from 'react';
import type { FileUpload } from '../../utils/types';
import { useFileContext } from '../../contexts/FileContext';
import * as fileService from '../../services/fileService';

interface FileItemProps {
    file: FileUpload;
}

const FileItem: React.FC<FileItemProps> = ({ file }) => {
    const { deleteFile } = useFileContext();

    const handleDownload = async () => {
        try {
            const blob = await fileService.downloadFile(file.id);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = file.original_filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
        } catch (error) {
            console.error('Download failed', error);
        }
    };

    return (
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <div>
                <p className="font-semibold">{file.original_filename}</p>
                <p className="text-sm text-gray-500">{file.file_size} bytes</p>
            </div>
            <div>
                <button onClick={handleDownload} className="text-blue-500 hover:text-blue-700 mr-4">Download</button>
                <button onClick={() => deleteFile(file.id)} className="text-red-500 hover:text-red-700">Delete</button>
            </div>
        </div>
    );
};

export default FileItem;
