import React, { useState, useEffect, useCallback } from 'react';
import { debounce } from 'lodash';
import { useFileContext } from '../../contexts/FileContext';
import FileItem from './FileItem';
import FilePreviewModal from './FilePreviewModal';
import { FiChevronDown, FiTrash2 } from 'react-icons/fi';
import { getFileTypes } from '../../services/fileService';
import type { SearchParams } from '../../utils/types';

export const FileList: React.FC = () => {
    const { fileData, loading, fetchPage, deleteFile, searchFiles, bulkDeleteFiles } = useFileContext();
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

    const handleBulkDelete = async () => {
        if (selectedFiles.length === 0) return;
        await bulkDeleteFiles(selectedFiles);
        setSelectedFiles([]);
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

                <div className="grid grid-cols-1 md:grid-cols-12 gap-4 mb-4 items-center">
                    <div className="md:col-span-4">
                        <input
                            type="text"
                            placeholder="Search files..."
                            value={queryInput}
                            onChange={(e) => setQueryInput(e.target.value)}
                            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>

                    {/* Start Date */}
                    <div className="md:col-span-2">
                        <input
                            type="date"
                            value={startDateInput}
                            onChange={(e) => setStartDateInput(e.target.value)}
                            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>

                    {/* End Date */}
                    <div className="md:col-span-2">
                        <input
                            type="date"
                            value={endDateInput}
                            onChange={(e) => setEndDateInput(e.target.value)}
                            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>

                    {/* File Type Dropdown */}
                    <div className="relative inline-block text-left md:col-span-2">
                        <div>
                            <button
                                type="button"
                                onClick={() => setIsFileTypeDropdownOpen(!isFileTypeDropdownOpen)}
                                className="inline-flex justify-center w-full rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-100 focus:ring-blue-500"
                            >
                                {selectedFileTypes.length === 0 ? 'All Types' : `${selectedFileTypes.length} types selected`}
                                <FiChevronDown className="-mr-1 ml-2 h-5 w-5" />
                            </button>
                        </div>
                        {isFileTypeDropdownOpen && (
                            <div className="origin-top-right absolute right-0 mt-2 w-full rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-10">
                                <div className="py-1 max-h-60 overflow-y-auto" role="menu" aria-orientation="vertical">
                                    {allFileTypes.map(fileType => (
                                        <a
                                            href="#"
                                            key={fileType}
                                            onClick={(e) => {
                                                e.preventDefault();
                                                handleFileTypeChange(fileType);
                                            }}
                                            className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                            role="menuitem"
                                        >
                                            <input
                                                type="checkbox"
                                                checked={selectedFileTypes.includes(fileType)}
                                                readOnly
                                                className="mr-2 h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                            />
                                            {fileType}
                                        </a>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Bulk Delete Button */}
                    <div className="md:col-span-2 flex justify-end">
                        {selectedFiles.length > 0 && (
                            <button
                                onClick={handleBulkDelete}
                                className="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 flex items-center"
                            >
                                <FiTrash2 className="mr-2" />
                                Delete ({selectedFiles.length})
                            </button>
                        )}
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
