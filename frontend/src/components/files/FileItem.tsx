import React from 'react';
import type { FileUpload } from '../../utils/types';
import * as fileService from '../../services/fileService';
import { FiEye, FiDownload, FiTrash2 } from 'react-icons/fi';
import { format } from 'date-fns';

interface FileItemProps {
    file: FileUpload;
    onDelete: (fileId: number) => void;
    onViewFile: (fileId: number) => void;
}

const FileItem: React.FC<FileItemProps> = ({ file, onDelete, onViewFile }) => {
    const handleDelete = (e: React.MouseEvent) => {
        e.stopPropagation();
        if (window.confirm(`Are you sure you want to delete ${file.original_filename}?`)) {
            onDelete(file.id);
        }
    };

    const handleDownload = (e: React.MouseEvent) => {
        e.stopPropagation();
        fileService.downloadFile(file.id)
            .then((blob: Blob) => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = file.original_filename;
                document.body.appendChild(a);
                a.click();
                a.remove();
            })
            .catch((error: any) => console.error('Download failed', error));
    };

    return (
        <tr className="hover:bg-gray-50 cursor-pointer" onClick={() => onViewFile(file.id)}>
            <td className="px-6 py-4 whitespace-nowrap">
                <div className="font-medium text-gray-900">{file.original_filename}</div>
            </td>
            <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                {(file.file_size / 1024).toFixed(2)} KB
            </td>
            <td className="px-6 py-4 whitespace-nowrap">
                <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                    {file.file_type}
                </span>
            </td>
            <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                {format(new Date(file.upload_date), 'MMM dd, yyyy')}
            </td>
            <td className="px-6 py-4 whitespace-nowrap text-right font-medium">
                <div className="flex items-center space-around space-x-4">
                    <button onClick={() => onViewFile(file.id)} className="text-gray-500 hover:text-blue-600">
                        <FiEye className="w-5 h-5" />
                    </button>
                    <button onClick={handleDownload} className="text-gray-500 hover:text-green-600">
                        <FiDownload className="w-5 h-5" />
                    </button>
                    <button onClick={handleDelete} className="text-gray-500 hover:text-red-600">
                        <FiTrash2 className="w-5 h-5" />
                    </button>
                </div>
            </td>
        </tr>
    );
};

export default FileItem;

