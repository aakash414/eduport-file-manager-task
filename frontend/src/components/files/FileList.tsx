// src/components/files/FileList.tsx
import React, { useEffect, useState } from 'react';
import { useFileContext } from '../../contexts/FileContext';
import FileItem from './FileItem';
import LoadingSpinner from '../common/LoadingSpinner';
import Pagination from '../common/Pagination';
import SearchBar from '../common/SearchBar';

const FileList: React.FC = () => {
    const { fileData, loading, error, fetchFiles } = useFileContext();
    const [currentPage, setCurrentPage] = useState(1);
    const [searchQuery, setSearchQuery] = useState('');

    useEffect(() => {
        fetchFiles(currentPage, searchQuery);
    }, [currentPage, searchQuery, fetchFiles]);

    if (loading) {
        return <LoadingSpinner />;
    }

    if (error) {
        return <p className="text-red-500">{error}</p>;
    }

    return (
        <div>
            <SearchBar onSearch={setSearchQuery} />
            {fileData && fileData.results.length > 0 ? (
                <>
                    {fileData.results.map((file) => (
                        <FileItem key={file.id} file={file} />
                    ))}
                    <Pagination
                        currentPage={currentPage}
                        totalPages={fileData.pagination.total_pages}
                        onPageChange={setCurrentPage}
                    />
                </>
            ) : (
                <p>No files found.</p>
            )}
        </div>
    );
};

export default FileList;
