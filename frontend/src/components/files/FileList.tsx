import React, { useState, useEffect, useCallback } from 'react';
import { useFileContext } from '../../contexts/FileContext';
import FileItem from './FileItem';
import type { SearchParams } from '../../utils/types';
import FilePreviewModal from './FilePreviewModal';
import { FiX, FiAlertCircle } from 'react-icons/fi';
import { debounce } from 'lodash';
import { useMemo } from 'react';

export const FileList: React.FC = () => {
    const { fileData, loading, error, fetchPage, deleteFile, searchFiles } = useFileContext();
    const [viewingFileId, setViewingFileId] = useState<number | null>(null);

    const [currentParams, setCurrentParams] = useState<SearchParams>({});

    // We keep separate state for the inputs to provide a responsive UI
    const [queryInput, setQueryInput] = useState('');
    const [fileTypeInput, setFileTypeInput] = useState('');
    const [startDateInput, setStartDateInput] = useState('');
    const [endDateInput, setEndDateInput] = useState('');

    const fileTypeOptions = useMemo(() => {
        if (!fileData?.results) return [];
        const types = new Set(fileData.results.map(file => file.file_type).filter(Boolean) as string[]);
        return Array.from(types).map(type => ({
            value: type,
            label: type.charAt(0).toUpperCase() + type.slice(1)
        }));
    }, [fileData]);

    const activeSearch = Object.keys(currentParams).length > 0;

    const debouncedSearch = useCallback(
        debounce((params: SearchParams) => {
            const isAnyFilterActive = Object.values(params).some(
                (value) => value !== undefined && (Array.isArray(value) ? value.length > 0 : true)
            );

            if (isAnyFilterActive) {
                searchFiles(params);
                setCurrentParams(params); // Store only filter values, not pagination
            } else if (activeSearch) {
                handleClearFilters();
            }
        }, 500),
        [activeSearch] // Re-create debounce if activeSearch changes to avoid stale closure
    );

    useEffect(() => {
        const params: SearchParams = {
            query: queryInput || undefined,
            file_type: fileTypeInput ? [fileTypeInput] : undefined,
            start_date: startDateInput || undefined,
            end_date: endDateInput || undefined,
        };
        debouncedSearch(params);

        return () => {
            debouncedSearch.cancel();
        };
    }, [queryInput, fileTypeInput, startDateInput, endDateInput, debouncedSearch]);

    const handleClearFilters = () => {
        setQueryInput('');
        setFileTypeInput('');
        setStartDateInput('');
        setEndDateInput('');
        setCurrentParams({});
        if (activeSearch) {
            searchFiles({});
        }
    };

    const handleDeleteFile = async (fileId: number) => {
        await deleteFile(fileId);
        // The view is now automatically refreshed by the useFiles hook
    };

    const handleNextPage = () => {
        fetchPage(fileData?.next ?? null);
    };

    const handlePreviousPage = () => {
        fetchPage(fileData?.previous ?? null);
    };

    // For Modal Navigation
    const fileIds = fileData?.results.map(f => f.id) || [];
    const currentFileIndex = viewingFileId ? fileIds.indexOf(viewingFileId) : -1;

    const handleNext = () => {
        if (currentFileIndex !== -1 && currentFileIndex < fileIds.length - 1) {
            setViewingFileId(fileIds[currentFileIndex + 1]);
        }
    };

    const handlePrevious = () => {
        if (currentFileIndex > 0) {
            setViewingFileId(fileIds[currentFileIndex - 1]);
        }
    };

    return (
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
            <div className="p-6">
                <h2 className="text-lg font-semibold text-gray-800 mb-4">My Files</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-4 mb-4">
                    <input
                        type="text"
                        placeholder="Search..."
                        value={queryInput}
                        onChange={(e) => setQueryInput(e.target.value)}
                        className="form-input w-full lg:col-span-2 xl:col-span-1"
                    />
                    <select
                        value={fileTypeInput}
                        onChange={(e) => setFileTypeInput(e.target.value)}
                        className="form-select w-full"
                    >
                        <option value="">All Types</option>
                        {fileTypeOptions.map(({ value, label }) => (
                            <option key={value} value={value}>{label}</option>
                        ))}
                    </select>
                    <input type="date" value={startDateInput} onChange={e => setStartDateInput(e.target.value)} className="form-input w-full" placeholder="Start Date" />
                    <input type="date" value={endDateInput} onChange={e => setEndDateInput(e.target.value)} className="form-input w-full" placeholder="End Date" />
                    <button
                        onClick={handleClearFilters}
                        className="text-sm text-gray-600 hover:text-gray-900 transition-colors flex items-center justify-center"
                    >
                        <FiX className="w-4 h-4 mr-1" />
                        Clear
                    </button>
                </div>
            </div>

            <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                    <thead className="bg-gray-50">
                        <tr>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Filename</th>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Size</th>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date Modified</th>
                            <th scope="col" className="relative px-6 py-3">
                                <span className="sr-only">Actions</span>
                            </th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {loading ? (
                            <tr><td colSpan={5} className="text-center py-12"><div className="spinner">Loading...</div></td></tr>
                        ) : error ? (
                            <tr><td colSpan={5} className="text-center py-12 text-red-600"><FiAlertCircle className="mx-auto w-10 h-10 mb-2" />{error}</td></tr>
                        ) : fileData?.results.length === 0 ? (
                            <tr><td colSpan={5} className="text-center py-12 text-gray-500">No files found.</td></tr>
                        ) : (
                            fileData?.results.map(file => (
                                <FileItem
                                    key={file.id}
                                    file={file}
                                    onDelete={handleDeleteFile}
                                    onViewFile={() => setViewingFileId(file.id)}
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

            {viewingFileId && (
                <FilePreviewModal
                    fileId={viewingFileId}
                    onClose={() => setViewingFileId(null)}
                    onNext={handleNext}
                    onPrevious={handlePrevious}
                    hasNext={currentFileIndex < fileIds.length - 1}
                    hasPrevious={currentFileIndex > 0}
                />
            )}
        </div>
    );
};
