import React from 'react';
import FileUpload from '../components/files/FileUpload';
import { FileList } from '../components/files/FileList';
import { FileProvider } from '../contexts/FileContext';

const Dashboard: React.FC = () => {
    return (
        <FileProvider>
            <div className="p-8">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
                    {/* Left Column: File Upload */}
                    <div className="lg:col-span-1">
                        <FileUpload />
                    </div>
                    {/* Right Column: File List */}
                    <div className="lg:col-span-2">
                        <FileList />
                    </div>
                </div>
            </div>
        </FileProvider>
    );
};

export default Dashboard;
