import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useFileContext } from '../../contexts/FileContext';
import FileItem from './FileItem';
import type { SearchParams } from '../../utils/types';
import FilePreviewModal from './FilePreviewModal';
import { FiX, FiChevronDown } from 'react-icons/fi';
import { debounce } from 'lodash';
import { getFileTypes } from '../../services/fileService';

export const FileList: React.FC = () => {
    const { fileData, loading, fetchPage, deleteFile, searchFiles } = useFileContext();
    const [previewingFileIndex, setPreviewingFileIndex] = useState<number | null>(null);



    const [queryInput, setQueryInput] = useState('');
    const [startDateInput, setStartDateInput] = useState('');
    const [endDateInput, setEndDateInput] = useState('');

    const [allFileTypes, setAllFileTypes] = useState<string[]>([]);
    const [selectedFileTypes, setSelectedFileTypes] = useState<string[]>([]);
    const [isFileTypeDropdownOpen, setIsFileTypeDropdownOpen] = useState(false);
    const fileTypeFilterRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const fetchFileTypes = async () => {
            try {
                const types = await getFileTypes();
                setAllFileTypes(types);
            } catch (error) {
                console.error("Failed to fetch file types:", error);
            }
        };
        fetchFileTypes();
    }, []);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (fileTypeFilterRef.current && !fileTypeFilterRef.current.contains(event.target as Node)) {
                setIsFileTypeDropdownOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);

    const debouncedSearch = useCallback(debounce(searchFiles, 500), [searchFiles]);

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
                ? prev.filter(ft => ft !== fileType)
                : [...prev, fileType]
        );
    };

    const handleClearFilters = () => {
        setQueryInput('');
        setSelectedFileTypes([]);
        setStartDateInput('');
        setEndDateInput('');

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
                    <div className="relative" ref={fileTypeFilterRef}>
                        <button
                            onClick={() => setIsFileTypeDropdownOpen(!isFileTypeDropdownOpen)}
                            className="w-full text-left flex justify-between items-center px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
                        >
                            <span className="text-gray-700">
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
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date Uploaded</th>
                            <th scope="col" className="relative px-6 py-3">
                                <span className="sr-only">Actions</span>
                            </th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {loading ? (
                            <tr><td colSpan={5} className="text-center py-12"><div className="spinner">Loading...</div></td></tr>
                        ) : fileData?.results?.length === 0 ? (
                            <tr><td colSpan={5} className="text-center py-12 text-gray-500">No files found.</td></tr>
                        ) : (
                            fileData?.results?.map((file, index) => (
                                <FileItem
                                    key={file.id}
                                    file={file}
                                    onDelete={handleDeleteFile}
                                    onViewFile={() => setPreviewingFileIndex(index)}
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
    );
};
