import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useFileContext } from '../../contexts/FileContext';
import { FiUploadCloud } from 'react-icons/fi';

const FileUpload: React.FC = () => {
    const { uploadFile, bulkUploadFiles, progress, loading } = useFileContext();
    const [error, setError] = useState<string | null>(null);

    const onDrop = useCallback(async (acceptedFiles: File[]) => {
        setError(null);
        if (acceptedFiles.length === 0) {
            return;
        }

        try {
            if (acceptedFiles.length === 1) {
                await uploadFile(acceptedFiles[0]);
            } else {
                await bulkUploadFiles(acceptedFiles);
            }
        } catch (err) {
            setError('Upload failed. Please try again.');
        }
    }, [uploadFile, bulkUploadFiles]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        multiple: true,
    });

    return (
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">Upload Files</h2>
            
            <div 
                {...getRootProps()} 
                className={`relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-300 ease-in-out
                ${isDragActive ? 'border-blue-500 bg-blue-50 scale-105 shadow-lg' : 'border-gray-300 bg-gray-50 hover:border-blue-400 hover:bg-blue-50'}`}
            >
                <input {...getInputProps()} />
                
                <div className="flex flex-col items-center justify-center space-y-3">
                    <FiUploadCloud className={`w-12 h-12 transition-colors duration-300 ${isDragActive ? 'text-blue-500' : 'text-gray-400'}`} />
                    <p className="text-gray-600 font-semibold">
                        {isDragActive ? "Drop files to upload" : "Drag & drop files here"}
                    </p>
                    <p className="text-sm text-gray-500">or</p>
                    <button 
                        type="button"
                        className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                    >
                        Choose Files
                    </button>
                </div>
            </div>

            {loading && (
                <div className="mt-4">
                    <h3 className="text-sm font-medium text-gray-700 mb-2">Uploading...</h3>
                    <div className="w-full bg-gray-200 rounded-full h-2.5">
                        <div 
                            className="bg-blue-600 h-2.5 rounded-full transition-all duration-300 ease-in-out" 
                            style={{ width: `${progress}%` }}
                        ></div>
                    </div>
                    <p className="text-right text-sm text-gray-500 mt-1">{progress}%</p>
                </div>
            )}

            {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
        </div>
    );
};

export default FileUpload;
