import React from 'react';
import FileUpload from '../components/files/FileUpload';
import { FileList } from '../components/files/FileList';
import { FileProvider } from '../contexts/FileContext';

const Dashboard: React.FC = () => {
    return (
        <FileProvider>
            <div className="p-8">
                <div className="grid grid-cols-1 gap-8 items-start">
                    <div className="">
                        <FileUpload />
                    </div>
                    <div className="">
                        <FileList />
                    </div>
                </div>
            </div>
        </FileProvider>
    );
};

export default Dashboard;
