// src/components/files/FileUpload.tsx
import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useFileContext } from '../../contexts/FileContext';

const FileUpload: React.FC = () => {
    const { uploadFile, progress, loading } = useFileContext();
    const [error, setError] = useState<string | null>(null);

    const onDrop = useCallback(async (acceptedFiles: File[]) => {
        setError(null);
        if (acceptedFiles.length > 0) {
            try {
                await uploadFile(acceptedFiles[0]);
            } catch (err) {
                setError('Upload failed. Please try again.');
            }
        }
    }, [uploadFile]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        multiple: false,
    });

    return (
        <div {...getRootProps()} className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${isDragActive ? 'border-blue-500 bg-blue-100' : 'border-gray-300 hover:border-gray-400'}`}>
            <input {...getInputProps()} />
            {loading ? (
                <div>
                    <p>Uploading...</p>
                    <div className="w-full bg-gray-200 rounded-full h-2.5">
                        <div className="bg-blue-600 h-2.5 rounded-full" style={{ width: `${progress}%` }}></div>
                    </div>
                    <p>{progress}%</p>
                </div>
            ) : (
                isDragActive ?
                    <p>Drop the files here ...</p> :
                    <p>Drag 'n' drop some files here, or click to select files</p>
            )}
            {error && <p className="text-red-500 mt-2">{error}</p>}
        </div>
    );
};

export default FileUpload;
