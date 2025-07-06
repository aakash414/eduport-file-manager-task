import React, { useState, useCallback } from 'react';
import { useFileContext } from '../../contexts/FileContext';

const HomePage: React.FC = () => {
    const { uploadFile, bulkUploadFiles, progress, uploadReport } = useFileContext();
    const [filesToUpload, setFilesToUpload] = useState<FileList | null>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            setFilesToUpload(e.target.files);
        }
    };

    const handleUpload = () => {
        if (!filesToUpload) return;

        if (filesToUpload.length === 1) {
            uploadFile(filesToUpload[0]);
        } else {
                        bulkUploadFiles(Array.from(filesToUpload));
        }
        setFilesToUpload(null); // Clear selection after upload
    };

    const onDragOver = useCallback((event: React.DragEvent<HTMLDivElement>) => {
        event.preventDefault();
    }, []);

    const onDrop = useCallback((event: React.DragEvent<HTMLDivElement>) => {
        event.preventDefault();
        if (event.dataTransfer.files && event.dataTransfer.files.length > 0) {
            setFilesToUpload(event.dataTransfer.files);
        }
    }, []);

    return (
        <div style={{ padding: '20px' }}>
            <h1>File Upload</h1>
            <div
                onDragOver={onDragOver}
                onDrop={onDrop}
                style={{
                    border: '2px dashed #ccc',
                    padding: '20px',
                    textAlign: 'center',
                    marginBottom: '20px',
                }}
            >
                <p>Drag and drop files here, or click to select files</p>
                <input
                    type="file"
                    multiple
                    onChange={handleFileChange}
                    style={{ display: 'block', margin: '10px auto' }}
                />
            </div>
            {filesToUpload && (
                <div>
                    <h3>Files to upload:</h3>
                    <ul>
                        {Array.from(filesToUpload).map((file, i) => (
                            <li key={i}>{file.name}</li>
                        ))}
                    </ul>
                    <button onClick={handleUpload}>Upload</button>
                </div>
            )}
            {progress > 0 && <p>Upload Progress: {progress}%</p>}

            {uploadReport && (
                <div>
                    <h3>Upload Report</h3>
                    {uploadReport.successful.length > 0 && (
                        <div>
                            <h4>Successful:</h4>
                            <ul>
                                {uploadReport.successful.map((file: any, i: number) => (
                                    <li key={i}>{file.original_filename || file.filename}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                    {uploadReport.failed.length > 0 && (
                        <div>
                            <h4>Failed:</h4>
                            <ul>
                                {uploadReport.failed.map((file: any, i: number) => (
                                    <li key={i}>{file.filename}: {file.error}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default HomePage;
