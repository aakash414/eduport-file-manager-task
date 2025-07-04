// src/pages/Dashboard.tsx
import React from 'react';
import FileUpload from '../components/files/FileUpload';
import FileList from '../components/files/FileList';
import { FileProvider } from '../contexts/FileContext';

const Dashboard: React.FC = () => {
    return (
        <FileProvider>
            <div className="container mx-auto p-4">
                <h1 className="text-2xl font-bold mb-4">File Dashboard</h1>
                <div className="mb-8">
                    <h2 className="text-xl font-semibold mb-2">Upload New File</h2>
                    <FileUpload />
                </div>
                <div>
                    <h2 className="text-xl font-semibold mb-2">My Files</h2>
                    <FileList />
                </div>
            </div>
        </FileProvider>
    );
};

export default Dashboard;
