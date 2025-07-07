import React, { useState, useEffect, useCallback } from 'react';
import { debounce } from 'lodash';
import { useFileContext } from '../../contexts/FileContext';
import FileItem from './FileItem';
import FilePreviewModal from './FilePreviewModal';
import { FiChevronDown, FiTrash2 } from 'react-icons/fi';
import { getFileTypes } from '../../services/fileService';
import type { SearchParams } from '../../utils/types';

export const FileList: React.FC = () => {
    const { fileData, loading, fetchPage, deleteFile, searchFiles } = useFileContext();
    const [previewingFileIndex, setPreviewingFileIndex] = useState<number | null>(null);
    const [selectedFiles, setSelectedFiles] = useState<number[]>([]);

    const [queryInput, setQueryInput] = useState('');
    const [startDateInput, setStartDateInput] = useState('');
    const [endDateInput, setEndDateInput] = useState('');

    const [allFileTypes, setAllFileTypes] = useState<string[]>([]);
    const [selectedFileTypes, setSelectedFileTypes] = useState<string[]>([]);
    const [isFileTypeDropdownOpen, setIsFileTypeDropdownOpen] = useState(false);

    useEffect(() => {
        getFileTypes().then(setAllFileTypes);
    }, []);

    const debouncedSearch = useCallback(
        debounce((params: SearchParams) => {
            searchFiles(params);
        }, 500),
        [searchFiles]
    );

    useEffect(() => {
        const params: SearchParams = {
            search: queryInput || undefined,
            file_types: selectedFileTypes.length > 0 ? selectedFileTypes : undefined,
            start_date: startDateInput || undefined,
            end_date: endDateInput || undefined,
        };
        debouncedSearch(params);

        return () => {
            debouncedSearch.cancel();
        };
    }, [queryInput, selectedFileTypes, startDateInput, endDateInput, debouncedSearch]);

    const handleFileTypeChange = (fileType: string) => {
        setSelectedFileTypes(prev =>
            prev.includes(fileType)
                ? prev.filter(t => t !== fileType)
                : [...prev, fileType]
        );
    };

    const handleSelectFile = (fileId: number) => {
        setSelectedFiles(prev => 
            prev.includes(fileId) 
                ? prev.filter(id => id !== fileId)
                : [...prev, fileId]
        );
    };

    const handleDeleteFile = async (fileId: number) => {
        await deleteFile(fileId);
    };

    const handleNextPage = () => {
        fetchPage(fileData?.next ?? null);
    };

    const handlePreviousPage = () => {
        fetchPage(fileData?.previous ?? null);
    };

    const handleNext = () => {
        if (previewingFileIndex !== null && fileData && previewingFileIndex < fileData.results.length - 1) {
            setPreviewingFileIndex(previewingFileIndex + 1);
        }
    };

    const handlePrevious = () => {
        if (previewingFileIndex !== null && previewingFileIndex > 0) {
            setPreviewingFileIndex(previewingFileIndex - 1);
        }
    };

    const handleViewFile = (index: number) => {
        setPreviewingFileIndex(index);
    };

    return (
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
            <div className="p-6">
                <h2 className="text-lg font-semibold text-gray-800 mb-4">My Files</h2>
                <div className="flex flex-col space-y-4">
                    <div className="flex space-x-4">
                        <div className="flex-1">
                            <div className="relative">
                                <input
                                    type="text"
                                    placeholder="Search files..."
                                    value={queryInput}
                                    onChange={(e) => setQueryInput(e.target.value)}
                                    className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                                <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500">
                                    Search
                                </span>
                            </div>
                        </div>
                        <div className="flex-1">
                            <div className="relative">
                                <input
                                    type="date"
                                    value={startDateInput}
                                    onChange={(e) => setStartDateInput(e.target.value)}
                                    className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                                <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500">
                                    Start Date
                                </span>
                            </div>
                        </div>
                        <div className="flex-1">
                            <div className="relative">
                                <input
                                    type="date"
                                    value={endDateInput}
                                    onChange={(e) => setEndDateInput(e.target.value)}
                                    className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                                <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500">
                                    End Date
                                </span>
                            </div>
                        </div>
                    </div>
                    <div className="flex space-x-4">
                        <div className="flex-1">
                            <div className="relative">
                                <button
                                    onClick={() => setIsFileTypeDropdownOpen(!isFileTypeDropdownOpen)}
                                    className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 flex justify-between items-center"
                                >
                                    <span>
                                        {selectedFileTypes.length > 0
                                            ? `${selectedFileTypes.length} type(s) selected`
                                            : 'All Types'}
                                    </span>
                                    <FiChevronDown className={`w-5 h-5 text-gray-400 transition-transform ${isFileTypeDropdownOpen ? 'rotate-180' : ''}`} />
                                </button>
                                {isFileTypeDropdownOpen && (
                                    <div className="absolute z-20 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-y-auto">
                                        <ul className="py-1">
                                            {allFileTypes.map(type => (
                                                <li key={type} className="px-3 py-2 text-gray-700 hover:bg-gray-100 flex justify-start">
                                                    <label className="flex items-center cursor-pointer ">
                                                        <input
                                                            type="checkbox"
                                                            checked={selectedFileTypes.includes(type)}
                                                            onChange={() => handleFileTypeChange(type)}
                                                            className="h-4 w-4 mx-2 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                                        />
                                                        <span className="capitalize">{type}</span>
                                                    </label>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                <div className="flex justify-between items-center mb-4">
                    <div className="flex items-center space-x-4">
                        <button
                            onClick={() => handleDeleteFile(selectedFiles[0])}
                            disabled={!selectedFiles.length}
                            className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                        >
                            <FiTrash2 className="w-5 h-5" />
                            <span>Delete Selected ({selectedFiles.length})</span>
                        </button>
                    </div>
                </div>
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Select
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Filename
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Size
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Type
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Uploaded By
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Date
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Actions
                                </th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {loading ? (
                                <tr><td colSpan={7} className="text-center py-12"><div className="spinner">Loading...</div></td></tr>
                            ) : fileData?.results?.length === 0 ? (
                                <tr><td colSpan={7} className="text-center py-12 text-gray-500">No files found.</td></tr>
                            ) : (
                                fileData?.results.map((file, index) => (
                                    <FileItem
                                        key={file.id}
                                        file={file}
                                        onDelete={handleDeleteFile}
                                        onViewFile={() => handleViewFile(index)}
                                        onToggleSelect={handleSelectFile}
                                        isSelected={selectedFiles.includes(file.id)}
                                    />
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                {fileData && (fileData.next || fileData.previous) && (
                    <div className="p-6 border-t border-gray-200 flex justify-between items-center">
                        <button
                            onClick={handlePreviousPage}
                            disabled={!fileData.previous || loading}
                            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Previous
                        </button>
                        <button
                            onClick={handleNextPage}
                            disabled={!fileData.next || loading}
                            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Next
                        </button>
                    </div>
                )}

                {previewingFileIndex !== null && fileData?.results && (
                    <FilePreviewModal
                        files={fileData.results}
                        currentIndex={previewingFileIndex}
                        onClose={() => setPreviewingFileIndex(null)}
                        onNext={handleNext}
                        onPrevious={handlePrevious}
                    />
                )}
            </div>
        </div>
    );
};
